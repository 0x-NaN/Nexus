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
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from asgi_correlation_id import CorrelationIdMiddleware, correlation_id
from pythonjsonlogger import jsonlogger

from app.database import database
from app.config import get_agent_definitions, get_policy_config
from app.ws_manager import manager
from app.routers import agents, transactions, kill_switch, simulator, auth
# Graceful degradation (fallback replay) is deferred to future work — see CONTEXT.md.
# from app.services.transaction_logger import is_db_healthy, replay_pending

# Configure structured JSON logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
# Clear existing handlers
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    '%(asctime)s %(levelname)s %(name)s %(correlation_id)s %(message)s'
)

# Custom filter to inject correlation ID into logs
class CorrelationIdFilter(logging.Filter):
    def filter(self, record):
        record.correlation_id = correlation_id.get() or '-'
        return True

logHandler.setFormatter(formatter)
logHandler.addFilter(CorrelationIdFilter())
logger.addHandler(logHandler)

app_logger = logging.getLogger(__name__)


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
    app_logger.info(f"Agents seeded: {len(get_agent_definitions())} agents")


async def _ensure_kill_switch_row():
    """Insert startup row only if table is empty."""
    count = await database.fetch_one("SELECT COUNT(*) AS cnt FROM kill_switch_events")
    if count["cnt"] == 0:
        await database.execute(
            "INSERT INTO kill_switch_events (state, triggered_by) VALUES ('active', 'system_startup')"
        )
        app_logger.info("Kill switch initialised → active")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await database.connect()
    app_logger.info("DB connected")
    await _seed_agents_from_config()
    await _ensure_kill_switch_row()
    # Graceful degradation (fallback JSONL replay on reconnect) is deferred to
    # future work — see CONTEXT.md. Removed from startup.
    # replayed = await replay_pending()
    # if replayed:
    #     app_logger.info(f"Replayed {replayed} pending fallback transactions into Postgres.")
    # Validate config loads without error
    get_policy_config()
    app_logger.info("Policy rules loaded")
    yield
    # Shutdown
    from app.simulator import engine as sim_engine
    sim_engine.stop()
    await database.disconnect()
    app_logger.info("DB disconnected")


app = FastAPI(
    title="Kill Switch — Governance API",
    description="Real-time policy enforcement and fleet-wide revocation for AI payment agents.",
    version="0.1.0",
    lifespan=lifespan,
)

# Add Correlation ID middleware
app.add_middleware(CorrelationIdMiddleware)

# CORS — open for local dev; lock down for any hosted demo
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOWED_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.routers import agents, transactions, kill_switch, simulator, auth, dev

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(agents.router)
app.include_router(transactions.router)
app.include_router(kill_switch.router)
app.include_router(simulator.router)
app.include_router(auth.router)
app.include_router(dev.router)


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


# ── Developer Tools ───────────────────────────────────────────────────────────
@app.post("/dev/reset-db", tags=["dev"])
async def reset_database():
    """Wipes the database and reseeds agents."""
    app_logger.warning("Force resetting database...")
    await database.execute("TRUNCATE TABLE transactions, kill_switch_events, agents CASCADE;")
    await _seed_agents_from_config()
    await _ensure_kill_switch_row()
    # Reset spend_total in memory if necessary or let DB reload handle it
    app_logger.warning("Database reset complete.")
    return {"status": "ok", "message": "Database wiped and reseeded"}


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health", tags=["meta"])
async def health():
    return {"status": "ok", "service": "kill-switch-api", "db": "connected"}
