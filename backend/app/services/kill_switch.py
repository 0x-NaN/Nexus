"""
services/kill_switch.py — Kill switch state reads.
Centralised so both the policy engine and the router use the same logic.
"""
from app.database import database


async def get_current_state() -> str:
    """Returns 'active' or 'killed' — current kill switch state."""
    row = await database.fetch_one("SELECT state FROM current_kill_switch")
    return row["state"] if row else "active"


async def is_killed() -> bool:
    return (await get_current_state()) == "killed"
