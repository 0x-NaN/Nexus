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

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen14b-opencode:latest"

HF_API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3"

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


def _build_ollama_payload(scenario: str) -> dict:
    return {
        "model": OLLAMA_MODEL,
        "prompt": f"{SYSTEM_PROMPT}\n\nUser: {scenario}\n\nAssistant:",
        "stream": False,
        "options": {"temperature": 0.7, "max_tokens": 1024},
    }


def _build_hf_payload(scenario: str) -> dict:
    return {
        "inputs": f"{SYSTEM_PROMPT}\n\nUser: {scenario}\n\nAssistant:",
        "parameters": {"temperature": 0.7, "max_new_tokens": 1024, "return_full_text": False},
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


async def _insert_denied_malformed(raw_response: str, source: str):
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
            "source":      source,
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
            "source": source,
        },
    })
    logger.warning(f"[LLM] Response FAILED -- malformed_agent_payload (inserted denied entry, source={source})")


async def _call_hf_api(scenario: str) -> Optional[str]:
    """Call HuggingFace Inference API. Returns raw response text or None on failure."""
    import os
    hf_token = os.getenv("HF_API_TOKEN")
    if not hf_token:
        return None

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(
                HF_API_URL,
                json=_build_hf_payload(scenario),
                headers={"Authorization": f"Bearer {hf_token}"},
            )
            if resp.status_code == 429:
                logger.warning("[LLM] Hosted API rate limited (429)")
                return None
            resp.raise_for_status()
            body = resp.json()
            if isinstance(body, list) and len(body) > 0:
                return body[0].get("generated_text", "")
            elif isinstance(body, dict):
                return body.get("generated_text", "") or body.get("error", "")
            return ""
    except httpx.TimeoutException:
        logger.warning("[LLM] Hosted API timeout")
        return None
    except httpx.HTTPStatusError as e:
        logger.warning(f"[LLM] Hosted API HTTP error: {e.response.status_code}")
        return None
    except Exception as e:
        logger.warning(f"[LLM] Hosted API error: {e}")
        return None


async def _call_ollama(scenario: str) -> Optional[str]:
    """Call local Ollama. Returns raw response text or None on failure."""
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                OLLAMA_URL,
                json=_build_ollama_payload(scenario),
            )
            resp.raise_for_status()
            body = resp.json()
            return body.get("response", "")
    except httpx.TimeoutException:
        logger.warning("[LLM] Ollama timeout")
        return None
    except httpx.ConnectError:
        logger.warning("[LLM] Ollama connection refused")
        return None
    except httpx.HTTPStatusError as e:
        logger.warning(f"[LLM] Ollama HTTP error: {e.response.status_code}")
        return None
    except Exception as e:
        logger.warning(f"[LLM] Ollama error: {e}")
        return None


async def _try_parse_and_build_txs(raw_response: str, source: str) -> Optional[list[TransactionIn]]:
    """Parse response and build TransactionIn objects. Returns list on success, None on parse failure."""
    if not raw_response or not raw_response.strip():
        return None

    cleaned = _strip_fences(raw_response)
    parsed = _parse_transactions(cleaned)

    if parsed is None:
        return None

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
                source=source,
            ))
        except (ValueError, TypeError, KeyError) as e:
            logger.warning(f"[LLM] Skipping invalid item {item}: {e}")
            continue

    return txs if txs else None


async def fetch_llm_transactions() -> list[TransactionIn]:
    """
    Three-tier LLM degradation:
    1. Hosted API (HuggingFace) -> source='llm-hosted'
    2. Local Ollama -> source='llm-local'
    3. Scripted generator -> source='sim'
    """
    scenario = _pick_scenario()
    logger.info(f"[LLM] Travel Agent scenario: {scenario[:70]}...")

    # --- Tier 1: Hosted API ---
    hf_response = await _call_hf_api(scenario)
    if hf_response is not None:
        txs = await _try_parse_and_build_txs(hf_response, "llm-hosted")
        if txs is not None:
            logger.info(f"[LLM] Hosted API success ({len(txs)} txs)")
            return txs
        # Malformed response from hosted API - deny and log, do NOT fall back
        await _insert_denied_malformed(hf_response, "llm-hosted")
        return []

    logger.info("[LLM] Hosted API unavailable — falling back to Ollama")

    # --- Tier 2: Local Ollama ---
    ollama_response = await _call_ollama(scenario)
    if ollama_response is not None:
        txs = await _try_parse_and_build_txs(ollama_response, "llm-local")
        if txs is not None:
            logger.info(f"[LLM] Ollama success ({len(txs)} txs)")
            return txs
        # Malformed response from Ollama - deny and log, do NOT fall back
        await _insert_denied_malformed(ollama_response, "llm-local")
        return []

    logger.warning("[LLM] Ollama unavailable — falling back to scripted generator")

    # --- Tier 3: Scripted generator (last resort) ---
    logger.warning("[LLM] All LLM tiers unavailable — Travel Agent using scripted generator")
    travel_agent = next(
        (a for a in get_agent_definitions() if a["id"] == TRAVEL_AGENT_ID), None
    )
    if not travel_agent:
        return []

    amount = Decimal(str(round(rnd.uniform(
        travel_agent["normal_range"]["min"],
        travel_agent["normal_range"]["max"]
    ), 2)))

    return [TransactionIn(
        agent_id=TRAVEL_AGENT_ID,
        amount=amount,
        category=travel_agent["category"],
        source="sim",
    )]


# Import at module level to avoid circular import issues
from app.config import get_agent_definitions