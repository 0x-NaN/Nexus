"""
main.py — FastAPI application entrypoint.

Startup sequence:
  1. Connect to DB
  2. Load & validate config (agents + policy rules)
  3. Upsert agents from config into DB
  4. Register all routers
  5. Mount WebSocket endpoint

CORS is open for dev — restrict in production.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.database import database
from app.config import get_agent_definitions, get_policy_config
from app.ws_manager import manager
from app.routers import agents, transactions, kill_switch, simulator, auth

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def _seed_agents_from_config():
    """Upsert agents from agents.yaml into DB on every startup."""
    for a in get_agent_definitions():
        await database.execute(
            """
            INSERT INTO agents
              (id, name, category, spend_cap, rate_limit, normal_range_min, normal_range_max)
            VALUES
              (:id, :name, :category, :spend_cap, :rate_limit, :min, :max)
            ON CONFLICT (id) DO UPDATE SET
              name             = EXCLUDED.name,
              category         = EXCLUDED.category,
              spend_cap        = EXCLUDED.spend_cap,
              rate_limit       = EXCLUDED.rate_limit,
              normal_range_min = EXCLUDED.normal_range_min,
              normal_range_max = EXCLUDED.normal_range_max
            """,
            {
                "id":        a["id"],
                "name":      a["name"],
                "category":  a["category"],
                "spend_cap": str(a["spend_cap"]),
                "rate_limit": a.get("rate_limit"),
                "min":       str(a["normal_range"]["min"]),
                "max":       str(a["normal_range"]["max"]),
            },
        )
    logger.info(f"Agents seeded: {len(get_agent_definitions())} agents")


async def _ensure_kill_switch_row():
    """Insert startup row only if table is empty."""
    count = await database.fetch_one("SELECT COUNT(*) AS cnt FROM kill_switch_events")
    if count["cnt"] == 0:
        await database.execute(
            "INSERT INTO kill_switch_events (state, triggered_by) VALUES ('active', 'system_startup')"
        )
        logger.info("Kill switch initialised → active")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await database.connect()
    logger.info("DB connected")
    await _seed_agents_from_config()
    await _ensure_kill_switch_row()
    # Validate config loads without error
    get_policy_config()
    logger.info("Policy rules loaded")
    yield
    # Shutdown
    from app.simulator import engine as sim_engine
    sim_engine.stop()
    await database.disconnect()
    logger.info("DB disconnected")


app = FastAPI(
    title="Kill Switch — Governance API",
    description="Real-time policy enforcement and fleet-wide revocation for AI payment agents.",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — open for local dev; lock down for any hosted demo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(agents.router)
app.include_router(transactions.router)
app.include_router(kill_switch.router)
app.include_router(simulator.router)
app.include_router(auth.router)


# ── WebSocket ─────────────────────────────────────────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            # Keep connection alive; dashboard doesn't send messages
            await ws.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(ws)


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health", tags=["meta"])
async def health():
    return {"status": "ok", "service": "kill-switch-api"}
