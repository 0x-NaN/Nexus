"""
routers/simulator.py — GET/POST /simulator/status|start|stop|inject
"""
from typing import Optional
from fastapi import APIRouter, HTTPException
from app.models import SimulatorStatusOut, SimulatorStartIn, InjectIn, LastInjection
from app.simulator import engine
from datetime import datetime

router = APIRouter(prefix="/simulator", tags=["simulator"])


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
