# Nexus — Project Context
**Last updated**: August 2026
**Status**: Active refactor — original hackathon folder recovered, evolving toward an industry-level open-source MVP.

---

## What Nexus Is
A real-time governance layer for fleets of autonomous AI payment-initiating agents. Sits between any agent and the transaction it wants to execute, evaluating every request against policy before allowing it through. An operator can instantly halt the entire fleet via a kill switch. Every decision — allowed, denied, or flagged — is permanently logged with a reason and exportable as CSV/TXT.

Originally built solo for [RazorPay Hackathon Name] (Theme: Governance Layer for Financial Agents). Now being refactored into a genuine open-source/small-org tool rather than a demo artifact.

---

## Current Architecture (stable, carry forward)
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
  React Dashboard (agent cards, live audit feed, kill switch, export, debug panel)
```

**Key design principle that must be preserved**: policy rules are config-defined at deploy time (YAML, loaded once at startup) and are NOT runtime-editable via any API. This is a deliberate security/governance choice.

---

## Tech Stack (current + planned additions)

| Layer | Current | Planned addition |
|---|---|---|
| Frontend | React + Vite + kokonut UI + bklit UI | motion.dev (functional motion only) |
| API | FastAPI (Python, async) | — |
| Policy | Python (in-process) | — |
| Primary DB | PostgreSQL | — |
| Real-time | WebSockets | — |
| LLM Agent | Ollama qwen2.5:3b (local, offline) | Hosted API fallback — deferred (graceful degradation) |
| Auth | Temporarily Disabled | JWT/OIDC implemented but bypassed. Deferred to endgame. |
| Deployment | Local only | Docker Compose — validation in progress |
| Dev tooling | OpenCode (blind) + Antigravity CLI | 5 MCPs configured in both tools |

---

## Agent Prompting References & Vibe-Coding Stack

### UI & Component Tools
- **kokonut UI** / **bklit UI** / **motion.dev**

### Design References
- **Taste skill**, **Awesome Design.md**, **frontend-design skill**, **Antigravity Kit (UI-UX Pro Max)**
- **Dev Metrics Dashboard Bento-Grid/Skeuomorphic Inspiration**: 
  - [Dark Glass/Skeuomorphic Dashboard Ref 1](https://d3tamksjp7q04h.cloudfront.net/2023/12/08060351/dashboard-1.jpg)
  - [Bento Grid Dashboard Ref 2](https://cdn.dribbble.com/userupload/45891063/file/fed11e31b499fc5e8259968c203dbdb3.png?format=webp&resize=400x300&vertical=center)

### Testing & Automation
- **Playwright CLI**

### Architecture References
- **fullstackopen**, **codecrafters.io**, **missing semester**

---

## Planned Additions (prioritized)

### Phase 1 — alongside this refactor
- [x] Auth (JWT/OIDC) — real multi-user support (bypassed for now)
- [x] MCP tooling for OpenCode
- [x] motion.dev integration (functional motion only)

### Phase 3 — Endgame UI/UX Polish (In Progress)
- [x] Comment out the Degradation Testing (LLM) panel.
- [x] Convert the Global Kill Switch into a skeuomorphic slider/toggle.
- [x] Implement Light/Dark mode toggle (color inversion/theme switching).
- [x] Add functional routing/views for sidebar items using Spatial UI.
- [x] Add Export function (TXT) for the Live Audit Trail.
- [x] Build Developer / Master Control dashboard for backend engineers (DB resets, Fleet Management).
- [x] Interactive dot particle background.
- [x] Update simulator engine to query database dynamically for newly added agents.
- [x] Implement brutalism/maximalism for the Light theme (add intense colors to dots/background so plain white isn't weird).
- [x] Fix burst detection bug (~50% catch rate) by refactoring simulator timing (await sequentially).

### Phase 4 — Future Works & Ideas
1. **Adaptive anomaly detection**: Flag statistically unusual transactions per agent even if within hard limits.
2. **Agent trust score**: Decaying reputation score per agent based on historical violation rate.
3. **Graceful Degradation** — DEFERRED (removed): The tier system (Hosted API → Local Ollama → Scripted fallback) and the transaction fallback/DEG logging (Postgres→JSONL, resolve button, DEG badges, TXT tags) were both commented out of the codebase and moved here. Rebuild when the core loop is stable.
4. **Dynamic Governance Compliance**: Ability to adjust or change the mechanics of an agent's working (e.g., what gets flagged) dynamically based on PDF or text entries uploaded by users that comply with governance acts like DPDP or EU Regulations.
5. **Authentication (JWT/OIDC)**: Fix the "Failed to fetch" (CORS / base URL issue) and fully support multi-tenant accounts. Currently deferred.

### Phase 5 — Hackathon Submission Hardening (ACTIVE)
**Hard deadline. Do not add anything beyond what is listed.**

- [x] **Fix 1 — Burst detection race condition**: Simulator burst injector fires transactions concurrently → policy engine evaluates against stale rate-check window. Fix: await each tx sequentially in the burst injector. Measure old vs new catch rate and report both numbers for README.
- [ ] **Fix 2 — Durable transaction logging / Postgres fallback**:
  - Create `log_transaction()` facade in `services/transaction_logger.py`. All callers use this — never the raw DB insert directly.
  - Inside: try Postgres first; on failure, append JSON line to `fallback_audit.jsonl`.
  - Add `replay_pending()`: on reconnect, insert pending lines in order, then clear the file.
  - System MUST fail closed for policy — logging failure never permits a transaction through.
- [ ] **Fix 3 — Health endpoint + UI status pill**:
  - Upgrade `GET /health` to return `{"db": "connected" | "fallback_active"}`.
  - Add a live status pill on the main dashboard (NOT the dev panel): green = connected, yellow = fallback_active. Updates live.
- [ ] **Fix 4 — Deployment (Railway + Netlify)**:
  - Frontend (React/Vite) → Netlify.
  - Backend (FastAPI) + PostgreSQL → Railway (persistent process, WebSocket support, managed Postgres).
  - Wire `VITE_API_BASE` / `VITE_WS_BASE` to Railway backend URL.
  - Goal: one hosted link a reviewer can open with zero local setup.

### Explicitly not planned
- Redis, n8n, Kubernetes/Kafka, GitHub Actions (CI/CD deleted for simplicity), Decision Narration, Dry Runs.

---


## Finalization Instruction
**When project is finalized (open-source MVP ready): remove all artifacts and mentions of Codestreet/AmEx from the codebase and replace with [RazorPay Hackathon Name] placeholders.** This includes:
- References in context.md, PRODUCT.md, DESIGN.md, presentation/ files
- Hackathon-specific language in comments, docs, and UI copy
- Repository name/origin references if different from final name