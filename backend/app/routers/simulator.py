"""
routers/simulator.py — GET/POST /simulator/status|start|stop|inject
"""
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.models import SimulatorStatusOut, SimulatorStartIn, InjectIn, LastInjection
from app.simulator import engine
from app.simulator.llm_agent import fetch_llm_transactions, _call_hf_api, _call_ollama, _try_parse_and_build_txs
from datetime import datetime

router = APIRouter(prefix="/simulator", tags=["simulator"])


class LLMTestRequest(BaseModel):
    tier: str  # "hosted", "ollama", "scripted", "auto"
    scenario: Optional[str] = None


class LLMTestResponse(BaseModel):
    tier_attempted: str
    tier_succeeded: Optional[str]
    transactions: list
    error: Optional[str] = None
    raw_response: Optional[str] = None


@router.post("/test-llm", response_model=LLMTestResponse)
async def test_llm_tier(body: LLMTestRequest):
    """Test a specific LLM degradation tier."""
    scenario = body.scenario or "Your client needs a round-trip flight from New York to Chicago departing next Monday and returning Wednesday."
    
    if body.tier == "hosted":
        raw = await _call_hf_api(scenario)
        if raw is None:
            return LLMTestResponse(
                tier_attempted="hosted",
                tier_succeeded=None,
                transactions=[],
                error="Hosted API unavailable (no token or network error)",
                raw_response=None
            )
        txs = await _try_parse_and_build_txs(raw, "llm-hosted")
        if txs is None:
            return LLMTestResponse(
                tier_attempted="hosted",
                tier_succeeded=None,
                transactions=[],
                error="Malformed response from hosted API",
                raw_response=raw[:500]
            )
        return LLMTestResponse(
            tier_attempted="hosted",
            tier_succeeded="llm-hosted",
            transactions=[tx.model_dump(mode="json") for tx in txs],
            raw_response=raw[:500]
        )
    
    elif body.tier == "scripted":
        from app.config import get_agent_definitions
        from app.models import TransactionIn
        from decimal import Decimal
        import random as rnd
        
        TRAVEL_AGENT_ID = "agent_003"
        travel_agent = next((a for a in get_agent_definitions() if a["id"] == TRAVEL_AGENT_ID), None)
        if not travel_agent:
            return LLMTestResponse(
                tier_attempted="scripted",
                tier_succeeded=None,
                transactions=[],
                error="Travel agent not found in config",
                raw_response=None
            )
        
        amount = Decimal(str(round(rnd.uniform(
            travel_agent["normal_range"]["min"],
            travel_agent["normal_range"]["max"]
        ), 2)))
        
        tx = TransactionIn(
            agent_id=TRAVEL_AGENT_ID,
            amount=amount,
            category=travel_agent["category"],
            source="sim",
        )
        
        return LLMTestResponse(
            tier_attempted="scripted",
            tier_succeeded="sim",
            transactions=[tx.model_dump(mode="json")],
            error=None,
            raw_response=None
        )
    
    elif body.tier == "ollama":
        raw = await _call_ollama(scenario)
        if raw is None:
            return LLMTestResponse(
                tier_attempted="ollama",
                tier_succeeded=None,
                transactions=[],
                error="Ollama unavailable (connection refused, timeout, or HTTP error)",
                raw_response=None
            )
        txs = await _try_parse_and_build_txs(raw, "llm-local")
        if txs is None:
            return LLMTestResponse(
                tier_attempted="ollama",
                tier_succeeded=None,
                transactions=[],
                error="Malformed response from Ollama",
                raw_response=raw[:500]
            )
        return LLMTestResponse(
            tier_attempted="ollama",
            tier_succeeded="llm-local",
            transactions=[tx.model_dump(mode="json") for tx in txs],
            raw_response=raw[:500]
        )
    
    elif body.tier == "auto":
        # Full three-tier test
        # Try hosted
        raw = await _call_hf_api(scenario)
        if raw is not None:
            txs = await _try_parse_and_build_txs(raw, "llm-hosted")
            if txs is not None:
                return LLMTestResponse(
                    tier_attempted="hosted",
                    tier_succeeded="llm-hosted",
                    transactions=[tx.model_dump(mode="json") for tx in txs],
                    raw_response=raw[:500]
                )
        
        # Fallback to Ollama
        raw = await _call_ollama(scenario)
        if raw is not None:
            txs = await _try_parse_and_build_txs(raw, "llm-local")
            if txs is not None:
                return LLMTestResponse(
                    tier_attempted="ollama",
                    tier_succeeded="llm-local",
                    transactions=[tx.model_dump(mode="json") for tx in txs],
                    raw_response=raw[:500]
                )
        
        # Last resort - scripted
        from app.config import get_agent_definitions
        from app.models import TransactionIn
        from decimal import Decimal
        import random as rnd
        
        TRAVEL_AGENT_ID = "agent_003"
        travel_agent = next((a for a in get_agent_definitions() if a["id"] == TRAVEL_AGENT_ID), None)
        if not travel_agent:
            return LLMTestResponse(
                tier_attempted="scripted",
                tier_succeeded=None,
                transactions=[],
                error="Travel agent not found in config",
                raw_response=None
            )
        
        amount = Decimal(str(round(rnd.uniform(
            travel_agent["normal_range"]["min"],
            travel_agent["normal_range"]["max"]
        ), 2)))
        
        tx = TransactionIn(
            agent_id=TRAVEL_AGENT_ID,
            amount=amount,
            category=travel_agent["category"],
            source="sim",
        )
        
        return LLMTestResponse(
            tier_attempted="scripted",
            tier_succeeded="sim",
            transactions=[tx.model_dump(mode="json")],
            error="All LLM tiers failed — used scripted fallback",
            raw_response=None
        )
    
    else:
        raise HTTPException(status_code=400, detail="Invalid tier. Use 'hosted', 'ollama', 'scripted', or 'auto'")


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
