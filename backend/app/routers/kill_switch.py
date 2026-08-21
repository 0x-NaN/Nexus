"""
routers/kill_switch.py — GET /kill-switch, POST /kill-switch, GET /kill-switch/history
"""
from fastapi import APIRouter
from app.database import database
from app.models import KillSwitchOut, KillSwitchIn, KillSwitchHistoryItem, KillSwitchState
from app.services.kill_switch import get_current_state
from app.ws_manager import manager

router = APIRouter(prefix="/kill-switch", tags=["kill-switch"])


async def _current_out() -> KillSwitchOut:
    row = await database.fetch_one("SELECT * FROM current_kill_switch")
    return KillSwitchOut(
        state=KillSwitchState(row["state"]),
        last_changed=row["timestamp"],
        triggered_by=row["triggered_by"],
    )


@router.get("", response_model=KillSwitchOut)
async def get_kill_switch():
    return await _current_out()


@router.post("", response_model=KillSwitchOut)
async def toggle_kill_switch(body: KillSwitchIn):
    current = await get_current_state()
    new_state = "killed" if current == "active" else "active"

    await database.execute(
        "INSERT INTO kill_switch_events (state, triggered_by) VALUES (:state, :by)",
        {"state": new_state, "by": body.triggered_by},
    )

    out = await _current_out()

    # Broadcast state change to all WS clients
    await manager.broadcast({
        "type": "kill_switch_event",
        "data": {
            "state":        out.state.value,
            "timestamp":    out.last_changed.isoformat(),
            "triggered_by": out.triggered_by,
        },
    })

    return out


@router.get("/history", response_model=list[KillSwitchHistoryItem])
async def kill_switch_history():
    rows = await database.fetch_all(
        "SELECT * FROM kill_switch_events ORDER BY timestamp ASC"
    )
    return [KillSwitchHistoryItem(**dict(r)) for r in rows]
