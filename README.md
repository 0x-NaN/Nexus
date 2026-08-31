# Nexus

<p align="center">
  <img src="https://img.shields.io/badge/version-0.1.0-blue.svg" alt="Version" />
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License" />
  <img src="https://img.shields.io/badge/python-3.12%2B-blue.svg" alt="Python" />
  <img src="https://img.shields.io/badge/react-19%2B-61dafb.svg" alt="React" />
  <img src="https://img.shields.io/badge/postgresql-17-blue.svg" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/docker-ready-blue.svg" alt="Docker" />
</p>

<p align="center">
  <strong>A real-time governance layer for fleets of autonomous AI payment-initiating agents</strong>
</p>

<p align="center">
  <img src="frontend/public/hero.png" alt="Nexus Dashboard" width="800" />
</p>

---

## Overview

Nexus sits between any AI agent and the transaction it wants to execute, evaluating every request against policy before allowing it through. An operator can instantly halt the entire fleet via a kill switch. Every decision — allowed, denied, or flagged — is permanently logged with a reason and exportable as CSV.

**Originally built for [RazorPay Hackathon 2026] (Theme: Governance Layer for Financial Agents). Now refactored toward an industry-level open-source MVP.**

---

## Architecture

```
Agent Fleet (4 scripted + 1 LLM-driven Travel Agent)
        │
        ▼
Policy Engine (kill_switch → scope_check → spend_cap → burst_detection)
First deny wins. Flag does not stop evaluation.
        │
        ▼
Event Log (PostgreSQL, append-only)
        │
        ▼
WebSocket Broadcast (server-push only)
        │
        ▼
React Dashboard (agent cards, live audit feed, kill switch, CSV export, debug panel)
```

**Key design principle**: Policy rules are config-defined at deploy time (YAML, loaded once at startup) and are NOT runtime-editable via any API.

---

## Features

| Feature | Description |
|---------|-------------|
| **Two-tier spend caps** | Flag at 90%, deny at 100% per agent |
| **Scope enforcement** | Agents locked to their category (grocery, subscription, travel, dining, office) |
| **Burst detection** | Rate limiting per agent (configurable per-agent) |
| **Global kill switch** | Instant fleet-wide revocation, logged as audit event |
| **Immutable audit trail** | Every transaction logged with decision + reason, exportable as CSV |
| **LLM degradation tiers** | Hosted API → Local Ollama → Scripted fallback |
| **Real-time dashboard** | WebSocket-fed agent cards, live audit feed, kill switch |

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 19 + Vite 6 + framer-motion |
| **Backend** | FastAPI (Python 3.12, async) |
| **Database** | PostgreSQL 17 |
| **Real-time** | WebSockets (server-push) |
| **LLM** | Vercel AI SDK + Ollama (qwen14b-opencode:latest) |
| **Deployment** | Docker Compose |
| **Design** | kokonut UI / bklit UI (shadcn-based registries) |

---

## Quick Start

### Prerequisites
- Docker Desktop 24+
- Node.js 20+ (for local frontend dev)
- Python 3.12+ (for local backend dev)
- Ollama (optional, for local LLM tier)

### Using Docker Compose (Recommended)

```bash
# Clone and configure
git clone https://github.com/0x-NaN/Nexus.git
cd Nexus

# Set required env vars
cp .env.example .env
# Edit .env: set POSTGRES_PASSWORD (required)

# Start all services
docker compose up --build
```

| Service | URL |
|---------|-----|
| Frontend Dashboard | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| WebSocket | ws://localhost:8000/ws |
| PostgreSQL | localhost:5432 |
| Ollama (optional) | http://localhost:11434 |

### Local Development

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
PGPASSWORD=postgres uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `POSTGRES_PASSWORD` | Yes | — | PostgreSQL password |
| `HF_API_TOKEN` | No | — | HuggingFace Inference API token (hosted LLM tier) |
| `OLLAMA_URL` | No | `http://host.docker.internal:11434/api/generate` | Ollama endpoint |
| `DATABASE_URL` | Auto | `postgresql+asyncpg://postgres:${POSTGRES_PASSWORD}@postgres:5432/killswitch` | DB connection |

---

## LLM Degradation Tiers

The Travel Agent uses a three-tier fallback system:

1. **Hosted API** (Primary) — HuggingFace Inference API, requires `HF_API_TOKEN`
2. **Local Ollama** (Fallback) — qwen14b-opencode:latest on localhost:11434
3. **Scripted Generator** (Last Resort) — Deterministic generator, system stays functional

Test tiers via API:
```bash
# Auto (all tiers)
curl -X POST http://localhost:8000/simulator/test-llm \
  -H "Content-Type: application/json" \
  -d '{"tier": "auto"}'

# Specific tier
curl -X POST http://localhost:8000/simulator/test-llm \
  -H "Content-Type: application/json" \
  -d '{"tier": "ollama"}'
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/agents` | List all agents with spend totals |
| `POST` | `/transaction/evaluate` | Submit transaction for policy evaluation |
| `GET` | `/transactions` | Query audit log (filters: agent_id, decision, etc.) |
| `GET` | `/transactions/export` | Export audit log as CSV |
| `GET` | `/kill-switch` | Current kill switch state |
| `POST` | `/kill-switch` | Toggle kill switch |
| `GET` | `/simulator/status` | Simulator status |
| `POST` | `/simulator/start` | Start noise simulator |
| `POST` | `/simulator/stop` | Stop simulator |
| `POST` | `/simulator/inject` | Inject misbehavior (overspend, off_scope, burst) |
| `POST` | `/simulator/test-llm` | Test LLM degradation tiers |

---

## Project Structure

```
Nexus/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entrypoint
│   │   ├── database.py          # DB connection
│   │   ├── config.py            # YAML config loader
│   │   ├── models.py            # Pydantic schemas
│   │   ├── ws_manager.py        # WebSocket manager
│   │   ├── routers/             # API routes
│   │   ├── services/            # Policy engine, kill switch
│   │   └── simulator/           # Noise + LLM agent
│   ├── config/
│   │   ├── agents.yaml          # Agent definitions
│   │   └── policy_rules.yaml    # Policy config
│   ├── db/
│   │   ├── schema.sql
│   │   ├── seed.sql
│   │   └── migrations/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Main dashboard
│   │   ├── main.jsx
│   │   └── index.css            # Design system
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── docker-compose.yml
├── .env.example
└── SETUP_AND_RUN_GUIDE.md
```

---

## Development

### Running Tests
```bash
# Backend
cd backend && python -m pytest

# Frontend
cd frontend && npm run lint
```

### Database Migrations
Migrations run automatically on container startup via PostgreSQL's `docker-entrypoint-initdb.d/`.

### Adding a Migration
```bash
# Create new migration file
touch backend/db/migrations/002_migration_name.sql
# Add SQL, then rebuild
docker compose up --build
```

---

## Future Work & Roadmap

| Feature | Status | Description |
|---------|--------|-------------|
| **Auth (JWT/OIDC)** | Planned | Account creation, login, and multi-tenant support. Currently deferred (bypassed in UI) to focus on core governance mechanics. |
| **Adaptive Anomaly Detection** | Planned | Flag statistically unusual transactions per agent even if within hard limits. |
| **Dynamic Governance Compliance** | Planned | Adjust agent policy via PDF/text uploads referencing DPDP or EU Regulations. |

---

## Deployment

### Railway (Backend & DB)
1. **Create a Railway project** and connect it to this GitHub repository.
2. In the Railway dashboard, go to **Variables** and add the required environment variable:
   - `POSTGRES_PASSWORD` – a strong password for the PostgreSQL service.
3. Railway will automatically detect the `docker-compose.yml` at the repo root. It will spin up the following services:
   - `backend` (FastAPI) – exposed on a generated URL, e.g. `https://my-project.up.railway.app`.
   - `postgres` – managed PostgreSQL instance.
   - `frontend` – you can optionally deploy the frontend separately on Netlify (see below).
4. After the first deployment, verify the API is reachable at `https://<railway-app>.up.railway.app/health`.
5. **Optional**: If you want the backend to serve the static frontend, uncomment the `frontend` service in `docker-compose.yml` and push the change – Railway will rebuild.

### Netlify (Frontend)
1. Sign in to Netlify and click **New site from Git**.
2. Connect the same GitHub repository and select the **frontend** folder as the base directory.
3. In **Build settings** set:
   - **Build command**: `cd frontend && npm install && npm run build`
   - **Publish directory**: `frontend/dist`
4. Add the following environment variables (replace the placeholder URL with your Railway backend URL):
   ```
   VITE_API_BASE=https://<railway-app>.up.railway.app
   VITE_WS_BASE=wss://<railway-app>.up.railway.app
   ```
5. Deploy – Netlify will build the Vite app and serve it at a Netlify subdomain.

### Quick local test before deployment
```bash
# Backend
cd backend && docker compose up --build
# Frontend (local dev)
cd frontend && npm install && npm run dev
```
Visit `http://localhost:5173` (frontend) and `http://localhost:8000/health` (backend) to ensure everything works.

---