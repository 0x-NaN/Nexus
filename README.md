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
  <img src="frontend/public/hero.jpg" alt="Nexus Dashboard" width="800" />
</p>

---

## Overview

Nexus sits between any AI agent and the transaction it wants to execute, evaluating every request against policy before allowing it through. An operator can instantly halt the entire fleet via a kill switch. Every decision — allowed, denied, or flagged — is permanently logged with a reason and exportable for review.

Nexus is a submission for **Razorpay's 2026 Build Fest — Open Track**. It doesn't fit the platform's commerce or fraud-detection tracks by design: it isn't building agentic checkout or scoring fraud probability, it's the control plane that would sit underneath either — policy enforcement, kill-switch revocation, and an immutable audit trail for any fleet of money-moving agents, regardless of what they're transacting or with whom.

**Why this matters now:** agent-to-agent commerce is projected to be enormous — analysts estimate AI agents could mediate trillions of dollars of global commerce within a few years — and most payment infrastructure today still assumes a human at checkout. Agent governance is lagging behind agent capability. Nexus is a small, honest attempt at closing that gap for teams who need real enforcement now, not a six-month platform evaluation.

---

## Architecture

```
Agent Fleet (4 scripted + 1 LLM-optional Travel Agent)
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
React Dashboard (agent cards, live audit feed, kill switch, export, dev console)
```

**Key design principle:** policy rules are config-defined at deploy time (YAML, loaded once at startup) and are **not** runtime-editable via any API. This is a deliberate governance choice, not an oversight — a policy layer that can be silently reconfigured at runtime isn't a policy layer worth trusting.

### Detailed Component Diagram

```mermaid
flowchart TD

subgraph group_ui["Operator UI"]
  node_frontend["React dashboard<br/>frontend<br/>[App.jsx]"]
  node_dashboard_layout["Dashboard layout<br/>UI shell"]
  node_auth_context["Auth context<br/>client session state<br/>[AuthContext.jsx]"]
end

subgraph group_api["Governance API"]
  node_api_app["FastAPI control plane<br/>API runtime<br/>[main.py]"]
  node_transaction_api["Transaction API<br/>router<br/>[transactions.py]"]
  node_agent_api["Agent API<br/>router<br/>[agents.py]"]
  node_kill_switch_api["Kill-switch API<br/>router<br/>[kill_switch.py]"]
  node_auth_service["Authentication<br/>router and service<br/>[auth.py]"]
  node_simulator_api["Simulator API<br/>router<br/>[simulator.py]"]
end

subgraph group_enforcement["Enforcement services"]
  node_policy_engine["Policy engine<br/>synchronous evaluator<br/>[policy_engine.py]"]
  node_policy_rules["Versioned policy rules<br/>YAML policy<br/>[policy_rules.yaml]"]
  node_agent_config["Agent fleet config<br/>YAML configuration<br/>[agents.yaml]"]
  node_kill_switch["Fleet kill switch<br/>revocation service<br/>[kill_switch.py]"]
  node_simulator["Agent simulator<br/>traffic generator<br/>[engine.py]"]
  node_llm_agent["Travel LLM agent<br/>optional agent behavior<br/>[llm_agent.py]"]
end

subgraph group_state["State and events"]
  node_transaction_logger["Transaction logger<br/>audit writer"]
  node_websocket_manager["WebSocket broadcaster<br/>event distribution<br/>[ws_manager.py]"]
  node_postgres[("PostgreSQL<br/>authoritative store<br/>[database.py]")]
  node_schema["Audit schema<br/>database schema<br/>[schema.sql]"]
end

subgraph group_runtime["Runtime dependencies"]
  node_compose{{"Docker Compose<br/>orchestration<br/>[docker-compose.yml]"}}
  node_ollama["Ollama<br/>optional local LLM"]
end

node_compose -->|"runs"| node_frontend
node_compose -->|"runs"| node_api_app
node_compose -->|"runs"| node_postgres
node_frontend -->|"renders"| node_dashboard_layout
node_frontend -->|"uses"| node_auth_context
node_frontend -->|"API requests"| node_api_app
node_websocket_manager -->|"live updates"| node_frontend
node_api_app -->|"mounts"| node_transaction_api
node_api_app -->|"mounts"| node_agent_api
node_api_app -->|"mounts"| node_kill_switch_api
node_api_app -->|"authenticates via"| node_auth_service
node_api_app -->|"mounts"| node_simulator_api
node_transaction_api -->|"evaluates transaction"| node_policy_engine
node_policy_engine -->|"checks first"| node_kill_switch
node_policy_engine -->|"loads at startup"| node_policy_rules
node_policy_engine -->|"loads at startup"| node_agent_config
node_policy_engine -->|"records decision"| node_transaction_logger
node_kill_switch_api -->|"changes state"| node_kill_switch
node_kill_switch -->|"records state change"| node_transaction_logger
node_agent_api -->|"manages agents"| node_postgres
node_transaction_logger -->|"writes audit"| node_postgres
node_schema -->|"defines"| node_postgres
node_transaction_logger -->|"broadcasts persisted decisions"| node_websocket_manager
node_kill_switch -->|"broadcasts state changes"| node_websocket_manager
node_simulator_api -->|"controls"| node_simulator
node_simulator -->|"submits transactions"| node_transaction_api
node_simulator -->|"uses travel behavior"| node_llm_agent
node_llm_agent -.->|"optional inference"| node_ollama

click node_compose "https://github.com/0x-nan/nexus/blob/main/docker-compose.yml"
click node_frontend "https://github.com/0x-nan/nexus/blob/main/frontend/src/App.jsx"
click node_dashboard_layout "https://github.com/0x-nan/nexus/blob/main/frontend/src/components/DashboardLayout.jsx"
click node_auth_context "https://github.com/0x-nan/nexus/blob/main/frontend/src/context/AuthContext.jsx"
click node_api_app "https://github.com/0x-nan/nexus/blob/main/backend/app/main.py"
click node_transaction_api "https://github.com/0x-nan/nexus/blob/main/backend/app/routers/transactions.py"
click node_agent_api "https://github.com/0x-nan/nexus/blob/main/backend/app/routers/agents.py"
click node_kill_switch_api "https://github.com/0x-nan/nexus/blob/main/backend/app/routers/kill_switch.py"
click node_auth_service "https://github.com/0x-nan/nexus/blob/main/backend/app/services/auth.py"
click node_simulator_api "https://github.com/0x-nan/nexus/blob/main/backend/app/routers/simulator.py"
click node_policy_engine "https://github.com/0x-nan/nexus/blob/main/backend/app/services/policy_engine.py"
click node_policy_rules "https://github.com/0x-nan/nexus/blob/main/backend/config/policy_rules.yaml"
click node_agent_config "https://github.com/0x-nan/nexus/blob/main/backend/config/agents.yaml"
click node_kill_switch "https://github.com/0x-nan/nexus/blob/main/backend/app/services/kill_switch.py"
click node_transaction_logger "https://github.com/0x-nan/nexus/blob/main/backend/app/services/transaction_logger.py"
click node_websocket_manager "https://github.com/0x-nan/nexus/blob/main/backend/app/ws_manager.py"
click node_postgres "https://github.com/0x-nan/nexus/blob/main/backend/app/database.py"
click node_schema "https://github.com/0x-nan/nexus/blob/main/backend/db/schema.sql"
click node_simulator "https://github.com/0x-nan/nexus/blob/main/backend/app/simulator/engine.py"
click node_llm_agent "https://github.com/0x-nan/nexus/blob/main/backend/app/simulator/llm_agent.py"

classDef toneNeutral fill:#f8fafc,stroke:#334155,stroke-width:1.5px,color:#0f172a
classDef toneBlue fill:#dbeafe,stroke:#2563eb,stroke-width:1.5px,color:#172554
classDef toneAmber fill:#fef3c7,stroke:#d97706,stroke-width:1.5px,color:#78350f
classDef toneMint fill:#dcfce7,stroke:#16a34a,stroke-width:1.5px,color:#14532d
classDef toneRose fill:#ffe4e6,stroke:#e11d48,stroke-width:1.5px,color:#881337
classDef toneIndigo fill:#e0e7ff,stroke:#4f46e5,stroke-width:1.5px,color:#312e81
classDef toneTeal fill:#ccfbf1,stroke:#0f766e,stroke-width:1.5px,color:#134e4a
class node_frontend,node_dashboard_layout,node_auth_context toneBlue
class node_api_app,node_transaction_api,node_agent_api,node_kill_switch_api,node_auth_service,node_simulator_api toneAmber
class node_policy_engine,node_policy_rules,node_agent_config,node_kill_switch,node_simulator,node_llm_agent toneMint
class node_transaction_logger,node_websocket_manager,node_postgres,node_schema toneRose
class node_compose,node_ollama toneIndigo
```

---

**Ecosystem-agnostic by design:** Nexus doesn't assume any particular agent framework, LLM provider, or payment protocol. It exposes a plain transaction-evaluation endpoint — any fleet that can call it is governable, whether the agents behind it are built on LangChain, CrewAI, a custom script, or something else entirely. Governance is decoupled from whatever stack is generating the transactions.

---

## Features

| Feature | Description |
|---|---|
| **Two-tier spend caps** | Flag at 90%, deny at 100% per agent |
| **Scope enforcement** | Agents locked to their category (grocery, subscription, travel, dining, office) |
| **Burst detection** | Per-agent rate limiting, evaluated sequentially to avoid race conditions under concurrent load |
| **Global kill switch** | Instant fleet-wide revocation, logged as an audit event |
| **Immutable audit trail** | Every transaction logged with a decision and a reason, exportable for review |
| **Framework-agnostic agent fleet** | Any agent stack that can call the evaluation endpoint is governable |
| **Real-time dashboard** | WebSocket-fed agent cards, live audit feed, kill switch, developer console |

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 19 + Vite 6, motion.dev (functional motion only), skeuomorphic + spatial UI design system |
| **Backend** | FastAPI (Python 3.12, async) |
| **Database** | PostgreSQL 17 |
| **Real-time** | WebSockets (server-push) |
| **LLM (optional)** | Local Ollama tier for the Travel Agent when available; falls back to a deterministic scripted generator otherwise |
| **Deployment** | Docker Compose (local) · Railway (backend + DB) · Netlify (frontend) |

---

## Quick Start

### Prerequisites
- Docker Desktop 24+
- Node.js 20+ (for local frontend dev)
- Python 3.12+ (for local backend dev)
- Ollama (optional — enables the local LLM tier for the Travel Agent)

### Using Docker Compose (Recommended)

```bash
git clone https://github.com/0x-NaN/Nexus.git
cd Nexus

cp .env.example .env
# Edit .env: set POSTGRES_PASSWORD (required)

docker compose up --build
```

| Service | URL |
|---|---|
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
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `POSTGRES_PASSWORD` | Yes | — | PostgreSQL password |
| `OLLAMA_URL` | No | `http://host.docker.internal:11434/api/generate` | Local Ollama endpoint, for the optional LLM tier |
| `DATABASE_URL` | Auto | `postgresql+asyncpg://postgres:${POSTGRES_PASSWORD}@postgres:5432/killswitch` | DB connection |

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/agents` | List all agents with spend totals |
| `POST` | `/agents` | Register a new agent |
| `DELETE` | `/agents/{agent_id}` | Remove an agent |
| `POST` | `/transaction/evaluate` | Submit a transaction for policy evaluation |
| `GET` | `/transactions` | Query the audit log (filters: agent_id, decision, etc.) |
| `GET` | `/transactions/export` | Export the audit log |
| `GET` | `/kill-switch` | Current kill switch state |
| `POST` | `/kill-switch` | Toggle kill switch |
| `GET` | `/simulator/status` | Simulator status |
| `POST` | `/simulator/start` \| `/simulator/stop` | Start / stop the ambient noise simulator |
| `POST` | `/simulator/inject` | Inject misbehavior (overspend, off_scope, burst) for testing |

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
│   │   └── simulator/           # Noise + Travel Agent
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
│   │   ├── App.jsx
│   │   ├── components/          # DashboardLayout, AgentCard, KillSwitchButton, etc.
│   │   └── index.css            # Design system
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── .env.example
└── SETUP_AND_RUN_GUIDE.md
```

---

## Business Case & Market Positioning

Enterprise-grade agent governance platforms already exist — Arthur AI, Credo AI, and Fiddler AI cover discovery, runtime guardrails, and compliance evidence across large, regulated organizations, and payment-focused platforms like Nevermined and Skyfire handle delegated spending and settlement across multiple agent protocols. These are serious, well-funded platforms, and Nexus isn't trying to compete with them at that scale.

The gap Nexus fills is different: **self-hosted, config-simple governance for small teams and independent builders** who need a kill switch, spend caps, and a real audit trail today — without a procurement cycle, a compliance certification process, or a hosted rules dashboard they don't control. Policy rules are YAML you own and version-control, not settings inside someone else's platform. Enforcement happens in-line at the point of transaction, not as after-the-fact monitoring.

Nexus isn't trying to be an enterprise governance suite at scale — it's the governance layer for the other 99% of teams shipping autonomous payment agents who need enforcement now.

---

## Development

```bash
# Backend tests
cd backend && python -m pytest

# Frontend lint
cd frontend && npm run lint
```

Database migrations run automatically on container startup via PostgreSQL's `docker-entrypoint-initdb.d/`.

---

## Misc.

<p align="center">
  <img src="frontend/public/FutureWorks.png" alt="Nexus Roadmap" width="800" />
</p>

---

## License

MIT License — see `LICENSE` file.

---

<p align="center">
  Built for autonomous AI governance.
</p>
