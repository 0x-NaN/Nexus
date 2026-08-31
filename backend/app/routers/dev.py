from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from pathlib import Path
import os

from app.database import database
from app.services.transaction_logger import is_db_healthy, get_simulate_db_failure, set_simulate_db_failure
# Graceful degradation (replay_pending) deferred to future work — see CONTEXT.md.
# from app.services.transaction_logger import replay_pending
from app.services.kill_switch import get_current_state
from app.routers.agents import list_agents
from app.routers.simulator import simulator_status

router = APIRouter(prefix="/dev", tags=["dev"])

FALLBACK_LOG_PATH = Path(os.getenv("FALLBACK_LOG_PATH", "/tmp/fallback_audit.jsonl"))

class ChaosMode(BaseModel):
    simulate_db_failure: bool

@router.post("/chaos/db-failure", summary="Toggle DB Failure Simulation")
async def toggle_chaos(mode: ChaosMode):
    set_simulate_db_failure(mode.simulate_db_failure)
    # ── Graceful degradation (auto-replay on restore) deferred — see CONTEXT.md ──
    # if not mode.simulate_db_failure:
    #     await replay_pending()
    return {"simulate_db_failure": get_simulate_db_failure()}


# ── /fallbacks/resolve — DEFERRED (graceful degradation) ──────────────────────
# @router.post("/fallbacks/resolve", summary="Resolve pending fallbacks via background process")
# async def resolve_fallbacks(background_tasks: BackgroundTasks):
#     """Spawns a background task (simulating a sub-agent) to process pending fallback logs."""
#     background_tasks.add_task(replay_pending)
#     return {"status": "resolution_agent_dispatched"}

@router.get("/metrics", summary="Development metrics endpoint")
async def dev_metrics():
    """Return an aggregated view of system health and metrics for the dev dashboard."""
    db_status = "connected" if is_db_healthy() else "fallback_active"
    kill_state = await get_current_state()
    
    # Retrieve data from other routers/services
    agents_list = await list_agents()
    sim_status = await simulator_status()
    
    # ── Fallback counts — DEFERRED (graceful degradation) ──────────────────────
    # pending_fallback_count = 0
    # if FALLBACK_LOG_PATH.exists():
    #     try:
    #         content = FALLBACK_LOG_PATH.read_text(encoding="utf-8").splitlines()
    #         pending_fallback_count = sum(1 for line in content if line.strip())
    #     except Exception:
    #         pending_fallback_count = -1
    # resolved_fallback_count = 0
    # total_fallback_count = 0
    # try:
    #     resolved_row = await database.fetch_one(
    #         "SELECT COUNT(*) AS cnt FROM transactions WHERE fallback_status = 'resolved'"
    #     )
    #     resolved_fallback_count = resolved_row["cnt"] if resolved_row else 0
    #     total_row = await database.fetch_one(
    #         "SELECT COUNT(*) AS cnt FROM transactions WHERE fallback_status IS NOT NULL"
    #     )
    #     total_fallback_count = total_row["cnt"] if total_row else 0
    # except Exception:
    #     pass

    # Calculate some aggregated stats
    total_spend = sum(float(a.spend_total) for a in agents_list) if agents_list else 0.0

    return {
        "db_status": db_status,
        "chaos_db_failure_active": get_simulate_db_failure(),
        "kill_switch": kill_state,
        # "pending_fallback_transactions": pending_fallback_count,
        # "resolved_fallback_transactions": resolved_fallback_count,
        # "total_fallback_transactions": total_fallback_count,
        "simulator_status": sim_status,
        "active_agents_count": len(agents_list),
        "total_fleet_spend": total_spend
    }

