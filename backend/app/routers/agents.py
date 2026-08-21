"""
routers/agents.py — GET /agents, GET /agents/{agent_id}
"""
from fastapi import APIRouter, HTTPException
from app.database import database
from app.models import AgentOut, AgentDetailOut, AgentStatus, TransactionOut
from app.services.kill_switch import get_current_state

router = APIRouter(prefix="/agents", tags=["agents"])


async def _agent_status() -> str:
    state = await get_current_state()
    return AgentStatus.halted if state == "killed" else AgentStatus.active


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
