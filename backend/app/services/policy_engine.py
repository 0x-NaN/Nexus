"""
services/policy_engine.py — Core transaction evaluation logic.
Evaluation order (from policy_rules.yaml):
  1. kill_switch   — if killed, deny everything immediately
  2. scope_check   — category must match agent's category
  3. spend_cap     — flag at 90%, deny at 100%
  4. burst         — tx count in last 60s vs rate_limit

First DENY wins and short-circuits. FLAG does NOT short-circuit.
"""
from decimal import Decimal
from datetime import datetime, timezone
from typing import Optional
import random
import string

from app.database import database
from app.models import Decision, TransactionIn, TransactionOut
from app.config import get_policy_config
from app.services.kill_switch import is_killed


def _generate_tx_id() -> str:
    now = datetime.now(timezone.utc)
    rand = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"txn_{now.strftime('%Y%m%d')}_{now.strftime('%H%M%S')}_{rand}"


async def evaluate(tx: TransactionIn) -> TransactionOut:
    policy = get_policy_config()["rules"]
    timestamp = datetime.now(timezone.utc)

    # ── Fetch agent ───────────────────────────────────────────────────────────
    agent = await database.fetch_one(
        "SELECT * FROM agents WHERE id = :id", {"id": tx.agent_id}
    )
    if not agent:
        raise ValueError(f"Agent not found: {tx.agent_id}")

    decision: Decision = Decision.allowed
    reason: Optional[str] = None

    # ── 1. Kill switch ────────────────────────────────────────────────────────
    if policy["kill_switch"]["enabled"] and await is_killed():
        decision = Decision.denied
        reason   = policy["kill_switch"]["deny_reason"]

    # ── 2. Scope check ────────────────────────────────────────────────────────
    if decision == Decision.allowed and policy["scope_check"]["enabled"]:
        if tx.category != agent["category"]:
            decision = Decision.denied
            reason   = policy["scope_check"]["deny_reason"]

    # ── 3. Spend cap ──────────────────────────────────────────────────────────
    if decision == Decision.allowed and policy["spend_cap"]["enabled"]:
        spend_row = await database.fetch_one(
            "SELECT spend_total FROM agent_spend_totals WHERE agent_id = :id",
            {"id": tx.agent_id},
        )
        spend_total = Decimal(str(spend_row["spend_total"])) if spend_row else Decimal("0")
        projected   = spend_total + tx.amount
        cap         = Decimal(str(agent["spend_cap"]))

        deny_threshold = cap * Decimal(str(policy["spend_cap"]["deny_threshold_pct"]))
        flag_threshold = cap * Decimal(str(policy["spend_cap"]["flag_threshold_pct"]))

        if projected >= deny_threshold:
            decision = Decision.denied
            reason   = policy["spend_cap"]["deny_reason"]
        elif projected >= flag_threshold:
            # Flag but continue evaluating remaining rules
            decision = Decision.flagged
            reason   = policy["spend_cap"]["flag_reason"]

    # ── 4. Burst detection ────────────────────────────────────────────────────
    if decision != Decision.denied and policy["burst_detection"]["enabled"]:
        rate_limit = agent["rate_limit"]
        if rate_limit is not None:
            rate_row = await database.fetch_one(
                "SELECT tx_count_last_60s FROM agent_recent_tx_rate WHERE agent_id = :id",
                {"id": tx.agent_id},
            )
            tx_count = rate_row["tx_count_last_60s"] if rate_row else 0
            if tx_count >= rate_limit:
                decision = Decision.denied
                reason   = policy["burst_detection"]["deny_reason"]

    # ── Write to event log ────────────────────────────────────────────────────
    tx_id = _generate_tx_id()
    misbehavior_type_str = (
        tx.misbehavior_type.value
        if tx.misbehavior_type and tx.misbehavior_type.value != "random"
        else None
    )

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
            "id":          tx_id,
            "agent_id":    tx.agent_id,
            "amount":      str(tx.amount),
            "category":    tx.category,
            "timestamp":   timestamp,
            "decision":    decision.value,
            "reason":      reason,
            "is_injected": tx.is_injected_misbehavior,
            "mtype":       misbehavior_type_str,
            "source":      tx.source,
        },
    )

    return TransactionOut(
        id=tx_id,
        agent_id=tx.agent_id,
        agent_name=agent["name"],
        amount=tx.amount,
        category=tx.category,
        timestamp=timestamp,
        decision=decision,
        reason=reason,
        is_injected_misbehavior=tx.is_injected_misbehavior,
        misbehavior_type=misbehavior_type_str,
        source=tx.source,
    )
