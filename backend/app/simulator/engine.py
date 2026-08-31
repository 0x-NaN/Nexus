"""
simulator/engine.py — Transaction Simulator

Two separate layers:
  1. Normal noise generator  — fires every normal_interval_ms, picks a random agent,
                               generates a plausible-but-varied transaction.
  2. Misbehavior injector    — on each normal tick, rolls injection_probability.
                               If hit: picks a random agent + random bad behavior.
                               Also callable directly via POST /simulator/inject.

Bad behavior types (hardcoded — these are YOUR test cases):
  overspend  — amount = cap * random(1.1, 1.5)          → triggers exceeds_spend_cap
  off_scope  — category = any OTHER category             → triggers off_scope_category
  burst      — fires N rapid evaluate calls (6–10, 150ms apart) → triggers burst_limit_exceeded

LLM layer (Travel Agent):
  On a separate timer inside the main loop, fires fetch_llm_transactions()
  as a fire-and-forget async task every LLM_INTERVAL_S seconds, regardless
  of which agent was randomly selected.  No cooldown gating by agent_id.
"""
import asyncio
import random
import logging
import time as time_module
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

import httpx

from app.config import get_agent_definitions, get_all_categories
from app.models import TransactionIn, MisbehaviorType
from app.simulator.llm_agent import fetch_llm_transactions, TRAVEL_AGENT_ID

logger = logging.getLogger(__name__)

# Internal endpoint (simulator calls the policy engine's REST API, same as a real agent would)
POLICY_ENGINE_URL = "http://localhost:8000"

LLM_INTERVAL_S = 3


class SimulatorState:
    def __init__(self):
        self.running: bool = False
        self.normal_interval_ms: int = 1500
        self.injection_probability: float = 0.15
        self.last_injection: Optional[dict] = None
        self._task: Optional[asyncio.Task] = None


_state = SimulatorState()
_tick_count: int = 0
_agent_totals: dict[str, int] = {}
_last_llm_time: float = 0.0
_llm_in_progress: bool = False


def get_state() -> SimulatorState:
    return _state


# ── Helpers ───────────────────────────────────────────────────────────────────

from app.database import database

async def _get_all_agents() -> list[dict]:
    rows = await database.fetch_all("SELECT * FROM agents")
    return [
        {
            "id": r["id"],
            "name": r["name"],
            "category": r["category"],
            "spend_cap": float(r["spend_cap"]),
            "rate_limit": r["rate_limit"],
            "normal_range": {
                "min": float(r["normal_range_min"]),
                "max": float(r["normal_range_max"])
            }
        }
        for r in rows
    ]

async def _random_agent() -> dict:
    agents = await _get_all_agents()
    return random.choice(agents) if agents else None


def _normal_tx(agent: dict) -> TransactionIn:
    amount = round(
        random.uniform(agent["normal_range"]["min"], agent["normal_range"]["max"]), 2
    )
    return TransactionIn(
        agent_id=agent["id"],
        amount=Decimal(str(amount)),
        category=agent["category"],
        is_injected_misbehavior=False,
        misbehavior_type=None,
    )


def _overspend_tx(agent: dict) -> TransactionIn:
    multiplier = random.uniform(1.1, 1.5)
    amount = round(float(agent["spend_cap"]) * multiplier, 2)
    return TransactionIn(
        agent_id=agent["id"],
        amount=Decimal(str(amount)),
        category=agent["category"],
        is_injected_misbehavior=True,
        misbehavior_type=MisbehaviorType.overspend,
    )


def _off_scope_tx(agent: dict) -> TransactionIn:
    all_cats = get_all_categories()
    other_cats = [c for c in all_cats if c != agent["category"]]
    bad_category = random.choice(other_cats)
    amount = round(
        random.uniform(agent["normal_range"]["min"], agent["normal_range"]["max"]), 2
    )
    return TransactionIn(
        agent_id=agent["id"],
        amount=Decimal(str(amount)),
        category=bad_category,
        is_injected_misbehavior=True,
        misbehavior_type=MisbehaviorType.off_scope,
    )


def _burst_txs(agent: dict) -> list[TransactionIn]:
    count = random.randint(6, 10)
    return [
        TransactionIn(
            agent_id=agent["id"],
            amount=Decimal(str(round(random.uniform(
                agent["normal_range"]["min"], agent["normal_range"]["max"]
            ), 2))),
            category=agent["category"],
            is_injected_misbehavior=True,
            misbehavior_type=MisbehaviorType.burst,
        )
        for _ in range(count)
    ]


def _build_injection(
    agent: dict,
    behavior: MisbehaviorType,
) -> list[TransactionIn]:
    if behavior == MisbehaviorType.overspend:
        return [_overspend_tx(agent)]
    elif behavior == MisbehaviorType.off_scope:
        return [_off_scope_tx(agent)]
    elif behavior == MisbehaviorType.burst:
        return _burst_txs(agent)
    return [_normal_tx(agent)]


# ── HTTP submit ───────────────────────────────────────────────────────────────

async def _submit(tx: TransactionIn):
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{POLICY_ENGINE_URL}/transaction/evaluate",
            json=tx.model_dump(mode="json"),
            timeout=5.0,
        )


# ── Fire-and-forget LLM call (runs in a separate task, does NOT block tick loop) ──

async def _do_llm_call():
    global _llm_in_progress
    try:
        logger.info("[LLM] Calling Ollama for Travel Agent...")
        try:
            txs = await fetch_llm_transactions()
        except Exception as e:
            logger.error(f"[LLM] Ollama crashed: {e}")
            txs = []
        if txs:
            for tx in txs:
                logger.info(f"[LLM] TX ${tx.amount} ({tx.category}) source={tx.source}")
                await _submit(tx)
        # ── Scripted degradation fallback — DEFERRED (see CONTEXT.md) ──────────
        # fetch_llm_transactions() now handles the Ollama → scripted path itself,
        # so this redundant fallback branch is removed.
        # else:
        #     agents = await _get_all_agents()
        #     travel_agent = next(
        #         (a for a in agents if a["id"] == TRAVEL_AGENT_ID), None
        #     )
        #     if travel_agent:
        #         logger.warning("[LLM] Empty — using scripted fallback with source=llm")
        #         tx = TransactionIn(...)
        #         await _submit(tx)
    except Exception as e:
        logger.error(f"[LLM] Unknown error in LLM task: {e}")
    finally:
        _llm_in_progress = False


# ── Core loop ─────────────────────────────────────────────────────────────────

async def _run_loop():
    global _tick_count, _agent_totals, _last_llm_time, _llm_in_progress
    logger.info("Simulator started")
    _tick_count = 0
    agents = await _get_all_agents()
    _agent_totals = {a["id"]: 0 for a in agents}
    _last_llm_time = 0.0
    _llm_in_progress = False
    try:
        while _state.running:
            await asyncio.sleep(_state.normal_interval_ms / 1000)

            if not _state.running:
                break

            # ── Fire LLM call on independent timer ─────────────────────
            now = time_module.time()
            if (
                now - _last_llm_time >= LLM_INTERVAL_S
                and not _llm_in_progress
            ):
                _last_llm_time = now
                _llm_in_progress = True
                asyncio.create_task(_do_llm_call())

            # ── Normal agent cycle ─────────────────────────────────────
            agent = await _random_agent()
            if not agent:
                continue
            _tick_count += 1
            _agent_totals[agent["id"]] = _agent_totals.get(agent["id"], 0) + 1

            # Roll for injection
            if random.random() < _state.injection_probability:
                behavior = random.choice([
                    MisbehaviorType.overspend,
                    MisbehaviorType.off_scope,
                    MisbehaviorType.burst,
                ])
                txs = _build_injection(agent, behavior)
                _state.last_injection = {
                    "agent_id": agent["id"],
                    "misbehavior_type": behavior.value,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                logger.info(f"[TICK {_tick_count}] INJECT {behavior.value} → {agent['name']} ({agent['id']})")
                for tx in txs:
                    await _submit(tx)
                    if behavior == MisbehaviorType.burst:
                        # 300ms gap: gives Postgres time to commit each tx so the
                        # agent_recent_tx_rate view reflects it before the next tx
                        # hits burst_detection. Old value (150ms) caused ~50% miss rate.
                        await asyncio.sleep(0.30)
            else:
                tx = _normal_tx(agent)
                logger.info(f"[TICK {_tick_count}] NORMAL ${tx.amount} → {agent['name']} ({agent['id']})")
                await _submit(tx)

            if _tick_count % 20 == 0:
                dist = ", ".join(f"{k}={v}" for k, v in sorted(_agent_totals.items()))
                logger.info(f"[SUMMARY @ tick {_tick_count}] Agent distribution: {dist}")
    except asyncio.CancelledError:
        pass
    logger.info("Simulator stopped")


# ── Public controls ───────────────────────────────────────────────────────────

def start(normal_interval_ms: int = 1500, injection_probability: float = 0.15):
    if _state.running:
        return
    _state.running = True
    _state.normal_interval_ms = normal_interval_ms
    _state.injection_probability = injection_probability
    _state._task = asyncio.create_task(_run_loop())


def stop():
    _state.running = False
    if _state._task:
        _state._task.cancel()
        _state._task = None


async def inject_now(
    agent_id: Optional[str],
    misbehavior_type: MisbehaviorType,
) -> list[dict]:
    """Manual override — called by POST /simulator/inject."""
    agents = await _get_all_agents()

    if agent_id:
        agent = next((a for a in agents if a["id"] == agent_id), None)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")
    else:
        agent = await _random_agent()

    # Resolve "random"
    if misbehavior_type == MisbehaviorType.random:
        misbehavior_type = random.choice([
            MisbehaviorType.overspend,
            MisbehaviorType.off_scope,
            MisbehaviorType.burst,
        ])

    txs = _build_injection(agent, misbehavior_type)

    _state.last_injection = {
        "agent_id": agent["id"],
        "misbehavior_type": misbehavior_type.value,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    results = []
    for tx in txs:
        await _submit(tx)
        if misbehavior_type == MisbehaviorType.burst:
            await asyncio.sleep(0.30)  # Match run-loop fix — give PG time to commit
        results.append(tx.model_dump(mode="json"))

    return results
