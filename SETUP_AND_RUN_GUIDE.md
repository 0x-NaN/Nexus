# Nexus — Setup & Run Guide

## Overview

Nexus is a real-time governance layer for AI payment agents with:
- **Backend**: FastAPI (Python 3.11+) + PostgreSQL + WebSockets
- **Frontend**: React 19 + Vite 6
- **Deployment**: Docker Compose (production), local processes (development)

---

## Prerequisites

### Local Development
| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.11+ | Backend runtime |
| Node.js | 20+ | Frontend build tooling |
| PostgreSQL | 15+ | Primary database |
| Ollama | Latest | Local LLM (optional, for Tier 2) |

### Production (Docker)
| Tool | Version |
|------|---------|
| Docker | 24+ |
| Docker Compose | v2+ |

---

## Quick Start (Local Development)

### 1. Database Setup
```bash
# Start PostgreSQL (if not running as service)
# Windows: Start-Service postgresql-x64-17
# Linux/macOS: sudo systemctl start postgresql

# Create database and user
psql -U postgres -c "CREATE DATABASE killswitch;"
psql -U postgres -c "CREATE USER postgres WITH PASSWORD 'postgres';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE killswitch TO postgres;"

# Run migrations
cd backend
PGPASSWORD=postgres psql -h localhost -U postgres -d killswitch -f db/schema.sql
PGPASSWORD=postgres psql -h localhost -U postgres -d killswitch -f db/seed.sql
PGPASSWORD=postgres psql -h localhost -U postgres -d killswitch -f db/migrations/001_source_column_update.sql
```

### 2. Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env  # Then edit: DATABASE_URL, HF_API_TOKEN (optional)

# Run
PGPASSWORD=postgres uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
# API: http://localhost:8000
# Health: http://localhost:8000/health
# Docs: http://localhost:8000/docs
```

### 3. Frontend
```bash
cd frontend
npm install
npm run dev
# Frontend: http://localhost:5173
```

### 4. Optional: Local LLM (Ollama)
```bash
# Install Ollama, then:
ollama pull qwen14b-opencode:latest
ollama serve
# Runs on http://localhost:11434
```

---

## Production Deployment (Docker Compose)

### docker-compose.yml
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:17-alpine
    environment:
      POSTGRES_DB: killswitch
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backend/db/schema.sql:/docker-entrypoint-initdb.d/01-schema.sql
      - ./backend/db/seed.sql:/docker-entrypoint-initdb.d/02-seed.sql
      - ./backend/db/migrations:/docker-entrypoint-initdb.d/migrations
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:${POSTGRES_PASSWORD}@postgres:5432/killswitch
      HF_API_TOKEN: ${HF_API_TOKEN}
      PYTHONUNBUFFERED: 1
    depends_on:
      postgres:
        condition: service_healthy
    ports:
      - "8000:8000"
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "5173:5173"
    depends_on:
      - backend
    restart: unless-stopped

  ollama:
    image: ollama/ollama:latest
    volumes:
      - ollama_data:/root/.ollama
    ports:
      - "11434:11434"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    profiles: ["gpu"]

volumes:
  postgres_data:
  ollama_data:
```

### backend/Dockerfile
```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### frontend/Dockerfile
```dockerfile
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 5173
CMD ["nginx", "-g", "daemon off;"]
```

### frontend/nginx.conf
```nginx
server {
    listen 5173;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    location /ws {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

### Deploy
```bash
# Set required env vars
export POSTGRES_PASSWORD="secure-random-password"
export HF_API_TOKEN="your-huggingface-token"  # Optional

docker compose up -d --build

# Check logs
docker compose logs -f backend
docker compose logs -f frontend
```

---

## Environment Variables

### Backend (.env)
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | - | `postgresql+asyncpg://user:pass@host:5432/db` |
| `HF_API_TOKEN` | No | - | HuggingFace Inference API token (Tier 1) |
| `PGPASSWORD` | For psql | - | PostgreSQL password for CLI tools |

### Frontend (.env)
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `VITE_API_BASE` | No | `http://localhost:8000` | Backend API URL |
| `VITE_WS_BASE` | No | `ws://localhost:8000/ws` | WebSocket URL |

---

## Common Issues & Fixes

---

## Common Issues & Fixes

---

## Database Reset

### From Backend (Recommended)

The backend provides a utility script to reset the database. This truncates all transaction and kill switch data and re-seeds the initial state.

```bash
# From backend directory
cd backend

# Option 1: Using the reset script (requires PGPASSWORD env)
PGPASSWORD=postgres python -m scratch.reset_db

# Option 2: Using psql directly
PGPASSWORD=postgres psql -h localhost -U postgres -d killswitch -c "
  TRUNCATE transactions, kill_switch_events RESTART IDENTITY;
  INSERT INTO kill_switch_events (state, triggered_by) VALUES ('active', 'system_startup');
"
```

### From Docker Compose

```bash
# Full reset including volumes (nuclear option)
docker compose down -v
docker compose up --build
```

### Reset via API (if endpoint exists)

Currently no dedicated reset endpoint exists. Use the script or Docker method above.

---

### "Bad Request" / 400 Errors
| Cause | Fix |
|-------|-----|
| Wrong API base URL in frontend | Check `VITE_API_BASE` matches backend host:port |
| WebSocket connection failed | Ensure `VITE_WS_BASE` uses `ws://` (not `http://`) |
| CORS blocked | Backend allows `*` in dev; configure `allow_origins` for prod |

### Terminal Spam / Multiple Windows
**Problem**: Running servers in separate PowerShell windows creates clutter.

**Solution**: Use Docker Compose (single command) or a process manager:
```bash
# Single terminal with Docker
docker compose up --build

# Or use a process manager locally
npm install -g concurrently
concurrently "cd backend && uvicorn app.main:app --reload" "cd frontend && npm run dev"
```

### Database Connection Failed
```bash
# Verify PostgreSQL is running
pg_isready -h localhost -p 5432

# Check DATABASE_URL format
postgresql+asyncpg://postgres:postgres@localhost:5432/killswitch
#                    ^user  ^pass  ^host  ^port  ^db
```

### Ollama 404 / Model Not Found
```bash
# Pull the correct model
ollama pull qwen14b-opencode:latest

# Verify
ollama list
curl http://localhost:11434/api/generate -d '{"model": "qwen14b-opencode:latest", "prompt": "test", "stream": false}'
```

---

## API Endpoints Reference

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/agents` | List all agents with spend totals |
| `POST` | `/transaction/evaluate` | Submit transaction for policy evaluation |
| `GET` | `/transactions` | Query audit log (filters: agent_id, decision, etc.) |
| `GET` | `/transactions/export` | Export CSV |
| `GET` | `/kill-switch` | Current kill switch state |
| `POST` | `/kill-switch` | Toggle kill switch |
| `GET` | `/simulator/status` | Simulator status |
| `POST` | `/simulator/start` | Start noise simulator |
| `POST` | `/simulator/stop` | Stop simulator |
| `POST` | `/simulator/inject` | Inject misbehavior (overspend, off_scope, burst) |
| `POST` | `/simulator/test-llm` | **Test LLM tiers** (hosted, ollama, scripted, auto) |

---

## LLM Degradation Tiers (Testing)

The `/simulator/test-llm` endpoint lets you test each tier from the UI or CLI:

```bash
# Test auto (hosted → ollama → scripted)
curl -X POST http://localhost:8000/simulator/test-llm \
  -H "Content-Type: application/json" \
  -d '{"tier": "auto"}'

# Test local Ollama only
curl -X POST http://localhost:8000/simulator/test-llm \
  -H "Content-Type: application/json" \
  -d '{"tier": "ollama"}'

# Test hosted API only (requires HF_API_TOKEN)
curl -X POST http://localhost:8000/simulator/test-llm \
  -H "Content-Type: application/json" \
  -d '{"tier": "hosted"}'

# Test scripted fallback
curl -X POST http://localhost:8000/simulator/test-llm \
  -H "Content-Type: application/json" \
  -d '{"tier": "scripted"}'
```

**Frontend**: Use the "LLM Degradation Test Panel" in the Simulator Debug section.

---

## Production Checklist

- [ ] Strong `POSTGRES_PASSWORD` (not `postgres`)
- [ ] `HF_API_TOKEN` set for hosted LLM tier
- [ ] CORS `allow_origins` restricted to your domain
- [ ] HTTPS termination (nginx/Cloudflare/traefik)
- [ ] Database backups configured
- [ ] Log aggregation (Loki, Datadog, etc.)
- [ ] Health checks wired to orchestrator (K8s, ECS, etc.)
- [ ] Resource limits on containers
- [ ] Ollama GPU profile enabled if using GPU

---

## File Structure
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
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Main dashboard
│   │   ├── main.jsx
│   │   └── index.css            # Design system
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   └── vite.config.js
├── docker-compose.yml
├── context.md                   # Project context (source of truth)
├── changes_log.txt              # Append-only session log
├── PRODUCT.md                   # Product definition
├── DESIGN.md                    # Design system spec
├── motion-design.md             # Motion policy
└── SETUP_AND_RUN_GUIDE.md       # This file
```