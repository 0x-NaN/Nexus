"""
routers/agents.py — GET /agents, GET /agents/{agent_id}
"""
from fastapi import APIRouter, HTTPException
from app.database import database
from app.models import AgentOut, AgentDetailOut, AgentStatus, TransactionOut
from app.services.kill_switch import get_current_state

router = APIRouter(prefix="/agents", tags=["agents"])


from pydantic import BaseModel

class AgentCreate(BaseModel):
    name: str
    category: str
    spend_cap: float
    rate_limit: float | None = None
    normal_range_min: float | None = 10.0
    normal_range_max: float | None = 100.0

async def _agent_status() -> str:
    state = await get_current_state()
    return AgentStatus.halted if state == "killed" else AgentStatus.active

@router.post("", response_model=AgentOut)
async def create_agent(agent: AgentCreate):
    import uuid
    agent_id = "agent-" + str(uuid.uuid4())[:8]
    
    await database.execute(
        """
        INSERT INTO agents
          (id, name, category, spend_cap, rate_limit, normal_range_min, normal_range_max)
        VALUES
          (:id, :name, :category, :spend_cap, :rate_limit, :min, :max)
        """,
        {
            "id": agent_id,
            "name": agent.name,
            "category": agent.category,
            "spend_cap": str(agent.spend_cap),
            "rate_limit": agent.rate_limit,
            "min": str(agent.normal_range_min),
            "max": str(agent.normal_range_max),
        }
    )
    
    # Return it via the view so spend_total is computed (0.0)
    status = await _agent_status()
    row = await database.fetch_one("SELECT * FROM agent_spend_totals WHERE agent_id = :id", {"id": agent_id})
    return AgentOut(
        id=row["agent_id"],
        name=row["name"],
        category=row["category"],
        spend_cap=row["spend_cap"],
        rate_limit=row["rate_limit"],
        spend_total=row["spend_total"],
        spend_pct=row["spend_pct"],
        status=status,
    )

@router.delete("/{agent_id}")
async def delete_agent(agent_id: str):
    # Check if exists
    row = await database.fetch_one("SELECT id FROM agents WHERE id = :id", {"id": agent_id})
    if not row:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Delete (ON DELETE CASCADE handles transactions, but let's be safe and explicitly delete transactions if needed)
    # The schema for transactions uses ON DELETE CASCADE for agent_id if it's set up that way. 
    # But let's manually delete transactions just to avoid foreign key errors if cascade is not defined.
    await database.execute("DELETE FROM transactions WHERE agent_id = :id", {"id": agent_id})
    await database.execute("DELETE FROM agents WHERE id = :id", {"id": agent_id})
    return {"status": "ok"}

@router.get("", response_model=list[AgentOut])
async def list_agents():
    status = await _agent_status()
    rows = await database.fetch_all("SELECT * FROM agent_spend_totals ORDER BY agent_id")
    return [
        AgentOut(
            id=r["agent_id"],
            name=r["name"],
            category=r["category"],
            spend_cap=r["spend_cap"],
            rate_limit=r["rate_limit"],
            spend_total=r["spend_total"],
            spend_pct=r["spend_pct"],
            status=status,
        )
        for r in rows
    ]


@router.get("/{agent_id}", response_model=AgentDetailOut)
async def get_agent(agent_id: str):
    status = await _agent_status()

    row = await database.fetch_one(
        "SELECT * FROM agent_spend_totals WHERE agent_id = :id",
        {"id": agent_id},
    )
    if not row:
        raise HTTPException(status_code=404, detail="Agent not found")

    recent = await database.fetch_all(
        """
        SELECT t.*, a.name AS agent_name
        FROM transactions t
        JOIN agents a ON a.id = t.agent_id
        WHERE t.agent_id = :id
        ORDER BY t.timestamp DESC
        LIMIT 10
        """,
        {"id": agent_id},
    )

    return AgentDetailOut(
        id=row["agent_id"],
        name=row["name"],
        category=row["category"],
        spend_cap=row["spend_cap"],
        rate_limit=row["rate_limit"],
        spend_total=row["spend_total"],
        spend_pct=row["spend_pct"],
        status=status,
        recent_transactions=[TransactionOut(**dict(r)) for r in recent],
    )
