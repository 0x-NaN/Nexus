"""
routers/simulator.py — GET/POST /simulator/status|start|stop|inject
"""
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.models import SimulatorStatusOut, SimulatorStartIn, InjectIn, LastInjection
from app.simulator import engine
# Graceful degradation (test-llm tier tester) deferred to future work — see CONTEXT.md.
# from app.simulator.llm_agent import fetch_llm_transactions, _call_hf_api, _call_ollama, _try_parse_and_build_txs
from datetime import datetime

router = APIRouter(prefix="/simulator", tags=["simulator"])


# class LLMTestRequest(BaseModel):
#     tier: str  # "hosted", "ollama", "scripted", "auto"
#     scenario: Optional[str] = None


# class LLMTestResponse(BaseModel):
#     tier_attempted: str
#     tier_succeeded: Optional[str]
#     transactions: list
#     error: Optional[str] = None
#     raw_response: Optional[str] = None


# @router.post("/test-llm", response_model=LLMTestResponse)
# async def test_llm_tier(body: LLMTestRequest):
#     """[DEFERRED — graceful degradation] Test a specific LLM degradation tier."""
#     ...
# [DEFERRED]     scenario = body.scenario or "Your client needs a round-trip flight from New York to Chicago departing next Monday and returning Wednesday."
# [DEFERRED]     
# [DEFERRED]     if body.tier == "hosted":
# [DEFERRED]         raw = await _call_hf_api(scenario)
# [DEFERRED]         if raw is None:
# [DEFERRED]             return LLMTestResponse(
# [DEFERRED]                 tier_attempted="hosted",
# [DEFERRED]                 tier_succeeded=None,
# [DEFERRED]                 transactions=[],
# [DEFERRED]                 error="Hosted API unavailable (no token or network error)",
# [DEFERRED]                 raw_response=None
# [DEFERRED]             )
# [DEFERRED]         txs = await _try_parse_and_build_txs(raw, "llm-hosted")
# [DEFERRED]         if txs is None:
# [DEFERRED]             return LLMTestResponse(
# [DEFERRED]                 tier_attempted="hosted",
# [DEFERRED]                 tier_succeeded=None,
# [DEFERRED]                 transactions=[],
# [DEFERRED]                 error="Malformed response from hosted API",
# [DEFERRED]                 raw_response=raw[:500]
# [DEFERRED]             )
# [DEFERRED]         return LLMTestResponse(
# [DEFERRED]             tier_attempted="hosted",
# [DEFERRED]             tier_succeeded="llm-hosted",
# [DEFERRED]             transactions=[tx.model_dump(mode="json") for tx in txs],
# [DEFERRED]             raw_response=raw[:500]
# [DEFERRED]         )
# [DEFERRED]     
# [DEFERRED]     elif body.tier == "scripted":
# [DEFERRED]         from app.config import get_agent_definitions
# [DEFERRED]         from app.models import TransactionIn
# [DEFERRED]         from decimal import Decimal
# [DEFERRED]         import random as rnd
# [DEFERRED]         
# [DEFERRED]         TRAVEL_AGENT_ID = "agent_003"
# [DEFERRED]         travel_agent = next((a for a in get_agent_definitions() if a["id"] == TRAVEL_AGENT_ID), None)
# [DEFERRED]         if not travel_agent:
# [DEFERRED]             return LLMTestResponse(
# [DEFERRED]                 tier_attempted="scripted",
# [DEFERRED]                 tier_succeeded=None,
# [DEFERRED]                 transactions=[],
# [DEFERRED]                 error="Travel agent not found in config",
# [DEFERRED]                 raw_response=None
# [DEFERRED]             )
# [DEFERRED]         
# [DEFERRED]         amount = Decimal(str(round(rnd.uniform(
# [DEFERRED]             travel_agent["normal_range"]["min"],
# [DEFERRED]             travel_agent["normal_range"]["max"]
# [DEFERRED]         ), 2)))
# [DEFERRED]         
# [DEFERRED]         tx = TransactionIn(
# [DEFERRED]             agent_id=TRAVEL_AGENT_ID,
# [DEFERRED]             amount=amount,
# [DEFERRED]             category=travel_agent["category"],
# [DEFERRED]             source="sim",
# [DEFERRED]         )
# [DEFERRED]         
# [DEFERRED]         return LLMTestResponse(
# [DEFERRED]             tier_attempted="scripted",
# [DEFERRED]             tier_succeeded="sim",
# [DEFERRED]             transactions=[tx.model_dump(mode="json")],
# [DEFERRED]             error=None,
# [DEFERRED]             raw_response=None
# [DEFERRED]         )
# [DEFERRED]     
# [DEFERRED]     elif body.tier == "ollama":
# [DEFERRED]         raw = await _call_ollama(scenario)
# [DEFERRED]         if raw is None:
# [DEFERRED]             return LLMTestResponse(
# [DEFERRED]                 tier_attempted="ollama",
# [DEFERRED]                 tier_succeeded=None,
# [DEFERRED]                 transactions=[],
# [DEFERRED]                 error="Ollama unavailable (connection refused, timeout, or HTTP error)",
# [DEFERRED]                 raw_response=None
# [DEFERRED]             )
# [DEFERRED]         txs = await _try_parse_and_build_txs(raw, "llm-local")
# [DEFERRED]         if txs is None:
# [DEFERRED]             return LLMTestResponse(
# [DEFERRED]                 tier_attempted="ollama",
# [DEFERRED]                 tier_succeeded=None,
# [DEFERRED]                 transactions=[],
# [DEFERRED]                 error="Malformed response from Ollama",
# [DEFERRED]                 raw_response=raw[:500]
# [DEFERRED]             )
# [DEFERRED]         return LLMTestResponse(
# [DEFERRED]             tier_attempted="ollama",
# [DEFERRED]             tier_succeeded="llm-local",
# [DEFERRED]             transactions=[tx.model_dump(mode="json") for tx in txs],
# [DEFERRED]             raw_response=raw[:500]
# [DEFERRED]         )
# [DEFERRED]     
# [DEFERRED]     elif body.tier == "auto":
# [DEFERRED]         # Full three-tier test
# [DEFERRED]         # Try hosted
# [DEFERRED]         raw = await _call_hf_api(scenario)
# [DEFERRED]         if raw is not None:
# [DEFERRED]             txs = await _try_parse_and_build_txs(raw, "llm-hosted")
# [DEFERRED]             if txs is not None:
# [DEFERRED]                 return LLMTestResponse(
# [DEFERRED]                     tier_attempted="hosted",
# [DEFERRED]                     tier_succeeded="llm-hosted",
# [DEFERRED]                     transactions=[tx.model_dump(mode="json") for tx in txs],
# [DEFERRED]                     raw_response=raw[:500]
# [DEFERRED]                 )
# [DEFERRED]         
# [DEFERRED]         # Fallback to Ollama
# [DEFERRED]         raw = await _call_ollama(scenario)
# [DEFERRED]         if raw is not None:
# [DEFERRED]             txs = await _try_parse_and_build_txs(raw, "llm-local")
# [DEFERRED]             if txs is not None:
# [DEFERRED]                 return LLMTestResponse(
# [DEFERRED]                     tier_attempted="ollama",
# [DEFERRED]                     tier_succeeded="llm-local",
# [DEFERRED]                     transactions=[tx.model_dump(mode="json") for tx in txs],
# [DEFERRED]                     raw_response=raw[:500]
# [DEFERRED]                 )
# [DEFERRED]         
# [DEFERRED]         # Last resort - scripted
# [DEFERRED]         from app.config import get_agent_definitions
# [DEFERRED]         from app.models import TransactionIn
# [DEFERRED]         from decimal import Decimal
# [DEFERRED]         import random as rnd
# [DEFERRED]         
# [DEFERRED]         TRAVEL_AGENT_ID = "agent_003"
# [DEFERRED]         travel_agent = next((a for a in get_agent_definitions() if a["id"] == TRAVEL_AGENT_ID), None)
# [DEFERRED]         if not travel_agent:
# [DEFERRED]             return LLMTestResponse(
# [DEFERRED]                 tier_attempted="scripted",
# [DEFERRED]                 tier_succeeded=None,
# [DEFERRED]                 transactions=[],
# [DEFERRED]                 error="Travel agent not found in config",
# [DEFERRED]                 raw_response=None
# [DEFERRED]             )
# [DEFERRED]         
# [DEFERRED]         amount = Decimal(str(round(rnd.uniform(
# [DEFERRED]             travel_agent["normal_range"]["min"],
# [DEFERRED]             travel_agent["normal_range"]["max"]
# [DEFERRED]         ), 2)))
# [DEFERRED]         
# [DEFERRED]         tx = TransactionIn(
# [DEFERRED]             agent_id=TRAVEL_AGENT_ID,
# [DEFERRED]             amount=amount,
# [DEFERRED]             category=travel_agent["category"],
# [DEFERRED]             source="sim",
# [DEFERRED]         )
# [DEFERRED]         
# [DEFERRED]         return LLMTestResponse(
# [DEFERRED]             tier_attempted="scripted",
# [DEFERRED]             tier_succeeded="sim",
# [DEFERRED]             transactions=[tx.model_dump(mode="json")],
# [DEFERRED]             error="All LLM tiers failed — used scripted fallback",
# [DEFERRED]             raw_response=None
# [DEFERRED]         )
# [DEFERRED]     
# [DEFERRED]     else:
# [DEFERRED]         raise HTTPException(status_code=400, detail="Invalid tier. Use 'hosted', 'ollama', 'scripted', or 'auto'")


@router.get("/status", response_model=SimulatorStatusOut)
async def simulator_status():
    s = engine.get_state()
    last = None
    if s.last_injection:
        last = LastInjection(
            agent_id=s.last_injection["agent_id"],
            misbehavior_type=s.last_injection["misbehavior_type"],
            timestamp=datetime.fromisoformat(s.last_injection["timestamp"]),
        )
    return SimulatorStatusOut(
        running=s.running,
        normal_interval_ms=s.normal_interval_ms,
        injection_probability=s.injection_probability,
        last_injection=last,
    )


@router.post("/start", response_model=SimulatorStatusOut)
async def simulator_start(body: Optional[SimulatorStartIn] = None):
    engine.start(
        normal_interval_ms=body.normal_interval_ms if body else 1500,
        injection_probability=body.injection_probability if body else 0.15,
    )
    return await simulator_status()


@router.post("/stop", response_model=SimulatorStatusOut)
async def simulator_stop():
    engine.stop()
    return await simulator_status()


@router.post("/inject")
async def simulator_inject(body: InjectIn):
    try:
        results = await engine.inject_now(
            agent_id=body.agent_id,
            misbehavior_type=body.misbehavior_type,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"injected": results}
