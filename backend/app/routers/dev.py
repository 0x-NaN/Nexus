from fastapi import APIRouter
from pydantic import BaseModel

from app.services.transaction_logger import get_simulate_db_failure, set_simulate_db_failure
from app.services.kill_switch import get_current_state
from app.routers.agents import list_agents
from app.routers.simulator import simulator_status

router = APIRouter(prefix="/dev", tags=["dev"])

class ChaosMode(BaseModel):
    simulate_db_failure: bool

@router.post("/chaos/db-failure", summary="Toggle DB Failure Simulation")
async def toggle_chaos(mode: ChaosMode):
    set_simulate_db_failure(mode.simulate_db_failure)
    return {"simulate_db_failure": get_simulate_db_failure()}


@router.get("/metrics", summary="Development metrics endpoint")
async def dev_metrics():
    """Return an aggregated view of system health and metrics for the dev dashboard."""
    kill_state = await get_current_state()
    
    # Retrieve data from other routers/services
    agents_list = await list_agents()
    sim_status = await simulator_status()
    
    # Calculate some aggregated stats
    total_spend = sum(float(a.spend_total) for a in agents_list) if agents_list else 0.0

    return {
        "chaos_db_failure_active": get_simulate_db_failure(),
        "kill_switch": kill_state,
        "simulator_status": sim_status,
        "active_agents_count": len(agents_list),
        "total_fleet_spend": total_spend
    }

