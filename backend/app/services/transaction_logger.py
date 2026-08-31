"""
services/transaction_logger.py — Durable transaction logging facade.

Single call point for recording any transaction. Callers (policy_engine,
routes) never touch the DB directly for transaction writes — they call
log_transaction() and this module decides where the record goes.

Guarantee:
  - Primary: PostgreSQL (via `database`).
  - Fallback: local JSONL file (FALLBACK_LOG_PATH) if Postgres raises.
  - Policy evaluation and logging are SEPARATE concerns.
    A logging failure NEVER permits a transaction — the policy decision
    is already made before log_transaction() is called.

Replay:
  replay_pending() reads the fallback file, inserts each row into Postgres
  in order, then clears the file. Call this on DB reconnect / health-check.
"""
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.database import database

logger = logging.getLogger(__name__)

# Fallback log lives next to the running process (writable at runtime).
FALLBACK_LOG_PATH = Path(os.getenv("FALLBACK_LOG_PATH", "/tmp/fallback_audit.jsonl"))

# In-memory flag so /health can reflect the current state accurately.
_db_healthy: bool = True
_simulate_db_failure: bool = False

def set_simulate_db_failure(state: bool):
    global _simulate_db_failure
    _simulate_db_failure = state

def get_simulate_db_failure() -> bool:
    return _simulate_db_failure

def is_db_healthy() -> bool:
    """Return current DB health state (updated by log_transaction)."""
    return _db_healthy

async def log_transaction(
    *,
    tx_id: str,
    agent_id: str,
    amount: str,
    category: str,
    timestamp: datetime,
    decision: str,
    reason: Optional[str],
    is_injected: bool,
    misbehavior_type: Optional[str],
    source: str,
) -> None:
    """
    Write a transaction record durably.

    Tries Postgres first. On any exception, falls back to a local JSONL file.
    Callers must not catch exceptions from this function — it handles its own
    fallback and should not propagate a logging failure upward.

    NOTE: This function does NOT make policy decisions. The decision is passed
    in as a plain string and recorded as-is.
    """
    global _db_healthy

    record = {
        "id": tx_id,
        "agent_id": agent_id,
        "amount": amount,
        "category": category,
        "timestamp": timestamp.isoformat(),
        "decision": decision,
        "reason": reason,
        "is_injected_misbehavior": is_injected,
        "misbehavior_type": misbehavior_type,
        "source": source,
    }

    try:
        if _simulate_db_failure:
            raise Exception("Chaos Engineering: Simulated Database Connection Drop")

        await database.execute(
            """
            INSERT INTO transactions
              (id, agent_id, amount, category, timestamp, decision, reason,
               is_injected_misbehavior, misbehavior_type, source)
            VALUES
              (:id, :agent_id, :amount, :category, :timestamp, :decision, :reason,
               :is_injected, :mtype, :source)
            """,
            {
                "id":          record["id"],
                "agent_id":    record["agent_id"],
                "amount":      record["amount"],
                "category":    record["category"],
                "timestamp":   timestamp,
                "decision":    record["decision"],
                "reason":      record["reason"],
                "is_injected": record["is_injected_misbehavior"],
                "mtype":       record["misbehavior_type"],
                "source":      record["source"],
            },
        )
        # Postgres write succeeded — mark healthy
        if not _db_healthy:
            logger.info("[transaction_logger] Postgres healthy again.")
            _db_healthy = True
            # Notify front‑end of healthy DB
            from app.ws_manager import manager
            await manager.broadcast({"type": "db_status", "db": "connected"})
        else:
            # DB already healthy – still ensure front‑end knows status (optional)
            pass

    except Exception as pg_err:
        # Postgres write failed — fall back to JSONL file
        logger.error(
            f"[transaction_logger] Postgres write failed ({pg_err}). "
            f"Falling back to JSONL file: {FALLBACK_LOG_PATH}"
        )
        _db_healthy = False
        # Notify front‑end of fallback state
        from app.ws_manager import manager
        await manager.broadcast({"type": "db_status", "db": "fallback_active"})
        _append_fallback(record)


def _append_fallback(record: dict) -> None:
    """Append a single transaction record as a JSON line to the fallback file."""
    try:
        with FALLBACK_LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, default=str) + "\n")
    except Exception as file_err:
        # Nothing left to do — log and move on. Policy is already decided.
        logger.critical(
            f"[transaction_logger] FALLBACK FILE WRITE ALSO FAILED: {file_err}. "
            f"Transaction {record.get('id')} is NOT durably stored."
        )


async def replay_pending() -> int:
    """
    Replay any transactions that were written to the fallback file while Postgres
    was unavailable. Inserts them into Postgres in order, then clears the file.

    Returns the count of replayed rows. Call this after confirming DB reconnect.
    """
    global _db_healthy

    if not FALLBACK_LOG_PATH.exists():
        return 0

    lines = FALLBACK_LOG_PATH.read_text(encoding="utf-8").splitlines()
    if not lines:
        return 0

    replayed = 0
    failed_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
            await database.execute(
                """
                INSERT INTO transactions
                  (id, agent_id, amount, category, timestamp, decision, reason,
                   is_injected_misbehavior, misbehavior_type, source)
                VALUES
                  (:id, :agent_id, :amount, :category, :timestamp, :decision, :reason,
                   :is_injected, :mtype, :source)
                ON CONFLICT (id) DO NOTHING
                """,
                {
                    "id":          record["id"],
                    "agent_id":    record["agent_id"],
                    "amount":      record["amount"],
                    "category":    record["category"],
                    "timestamp":   record["timestamp"],
                    "decision":    record["decision"],
                    "reason":      record["reason"],
                    "is_injected": record["is_injected_misbehavior"],
                    "mtype":       record["misbehavior_type"],
                    "source":      record["source"],
                },
            )
            replayed += 1
        except Exception as e:
            logger.error(f"[replay_pending] Failed to replay line: {e} — keeping it.")
            failed_lines.append(line)

    # Rewrite the file with only the lines that failed to replay
    if failed_lines:
        FALLBACK_LOG_PATH.write_text("\n".join(failed_lines) + "\n", encoding="utf-8")
    else:
        FALLBACK_LOG_PATH.unlink(missing_ok=True)
        _db_healthy = True

    logger.info(f"[replay_pending] Replayed {replayed} pending transactions.")
    return replayed
