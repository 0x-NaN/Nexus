import json
import logging
import random as rnd
import string
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

import httpx

from app.models import TransactionIn

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:3b"

TRAVEL_AGENT_ID = "agent_003"

SCENARIOS = [
    {"scenario": "Your client is stranded at the airport due to a cancelled flight. Book a hotel for a reasonable amount, a new flight, and arrange ground transport to the hotel. Return each as a separate transaction.", "weight": 3},
    {"scenario": "Your client needs an urgent last-minute international flight. Book it and also cover their airport lounge access for the wait.", "weight": 3},
    {"scenario": "Your client is on a business trip and needs to book a conference room for a client meeting, order lunch for the team, and book a taxi back to the hotel.", "weight": 2},
    {"scenario": "Your client needs a round-trip flight from New York to Chicago departing next Monday and returning Wednesday.", "weight": 2},
    {"scenario": "Your client is planning a weekend getaway and needs a hotel booking for two nights in San Francisco.", "weight": 2},
    {"scenario": "Your client needs to book a train ticket from Boston to Washington DC for next Friday morning.", "weight": 1},
]

SYSTEM_PROMPT = (
    'You are the Travel Agent, an AI authorized to make travel-related purchases on behalf of a client. '
    'Your allowed transaction category is "travel". '
    'The valid categories are: grocery, subscription, travel, dining, office. '
    'You must respond with ONLY a raw JSON array of transaction objects. '
    'No markdown, no code fences, no explanation \u2014 just the JSON array. '
    'Each object must have:\n'
    '  - "amount": a number in USD (positive, max 2000)\n'
    '  - "category": one of the valid categories listed above\n'
    '  - "description": a short string describing the purchase\n\n'
    'Do NOT wrap the response in markdown code fences. '
    'Return ONLY the raw JSON array.'
)

_weights = [s["weight"] for s in SCENARIOS]
_choices = [s["scenario"] for s in SCENARIOS]


def _pick_scenario() -> str:
    return rnd.choices(_choices, weights=_weights, k=1)[0]


def _build_payload(scenario: str) -> dict:
    return {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": scenario},
        ],
        "stream": False,
        "options": {"temperature": 0.7, "max_tokens": 1024},
    }


def _strip_fences(raw: str) -> str:
    lines = raw.strip().splitlines()
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            continue
        cleaned.append(line)
    result = "\n".join(cleaned).strip()
    if not result.startswith("["):
        idx = result.find("[")
        if idx >= 0:
            result = result[idx:]
    idx = result.rfind("]")
    if idx >= 0:
        result = result[: idx + 1]
    return result


def _parse_transactions(raw_json: str) -> Optional[list[dict]]:
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, list):
        return None
    for item in data:
        if not isinstance(item, dict):
            return None
        if "amount" not in item or "category" not in item:
            return None
    return data


async def _insert_denied_malformed(raw_response: str):
    from app.database import database
    from app.ws_manager import manager

    now = datetime.now(timezone.utc)
    tx_id = "txn_" + now.strftime("%Y%m%d_%H%M%S") + "_" + "".join(rnd.choices(string.ascii_lowercase + string.digits, k=6))

    agent = await database.fetch_one(
        "SELECT name FROM agents WHERE id = :id", {"id": TRAVEL_AGENT_ID}
    )
    agent_name = agent["name"] if agent else "Travel Agent"

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
            "agent_id":    TRAVEL_AGENT_ID,
            "amount":      "0.01",
            "category":    "travel",
            "timestamp":   now,
            "decision":    "denied",
            "reason":      "malformed_agent_payload",
            "is_injected": False,
            "mtype":       None,
            "source":      "llm",
        },
    )

    await manager.broadcast({
        "type": "transaction_event",
        "data": {
            "id": tx_id,
            "agent_id": TRAVEL_AGENT_ID,
            "agent_name": agent_name,
            "amount": "0.01",
            "category": "travel",
            "timestamp": now.isoformat(),
            "decision": "denied",
            "reason": "malformed_agent_payload",
            "is_injected_misbehavior": False,
            "misbehavior_type": None,
            "source": "llm",
        },
    })
    logger.warning("[LLM] Response FAILED -- malformed_agent_payload (inserted denied entry)")


async def fetch_llm_transactions() -> list[TransactionIn]:
    scenario = _pick_scenario()
    logger.info(f"[LLM] Calling Ollama ({MODEL}) for Travel Agent -- {scenario[:70]}...")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                OLLAMA_URL,
                json=_build_payload(scenario),
            )
            resp.raise_for_status()
            body = resp.json()
            content = body.get("message", {}).get("content", "")
    except Exception as e:
        logger.error(f"[LLM] API call FAILED: {e}")
        await _insert_denied_malformed(str(e))
        return []

    if not content.strip():
        logger.warning("[LLM] Empty response -- inserting denied entry")
        await _insert_denied_malformed("(empty response)")
        return []

    cleaned = _strip_fences(content)
    parsed = _parse_transactions(cleaned)

    if parsed is None:
        logger.warning(f"[LLM] Response FAILED to parse -- raw:\n{content[:300]}")
        await _insert_denied_malformed(content[:500])
        return []

    txs = []
    for item in parsed:
        try:
            amount = Decimal(str(item["amount"]))
            if amount <= 0:
                amount = Decimal("0.01")
            txs.append(TransactionIn(
                agent_id=TRAVEL_AGENT_ID,
                amount=amount,
                category=str(item["category"]),
                source="llm",
            ))
        except (ValueError, TypeError, KeyError) as e:
            logger.warning(f"[LLM] Skipping invalid item {item}: {e}")
            continue

    logger.info(f"[LLM] Response received -- parsed OK ({len(txs)} transaction(s))")
    return txs
