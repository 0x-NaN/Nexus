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
| LLM Agent | Ollama qwen2.5:3b (local, offline) | Hosted API primary + Ollama fallback |
| Auth | Temporarily Disabled | JWT/OIDC implemented but bypassed. Deferred to endgame. |
| Deployment | Local only | Docker Compose — validation in progress |
| Dev tooling | OpenCode (blind) + Antigravity CLI | 5 MCPs configured in both tools |

---

## Agent Prompting References & Vibe-Coding Stack

### UI & Component Tools
- **kokonut UI** / **bklit UI** / **motion.dev**

### Design References
- **Taste skill**, **Awesome Design.md**, **frontend-design skill**, **Antigravity Kit (UI-UX Pro Max)**

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
- [ ] Implement brutalism/maximalism for the Light theme (add intense colors to dots/background so plain white isn't weird).
- [ ] Fix burst detection bug (~50% catch rate) by refactoring simulator timing (await sequentially).
- [ ] Fix Auth "Failed to fetch" (CORS / base URL issue).

### Phase 4 — Future Works & Ideas
1. **Observability Stack**: Prometheus + Grafana (removed from current compose to save resources, but planned for hosted deployments).
2. **Graceful Degradation**: Solidify the tier system (Hosted API → Local Ollama → Scripted fallback). Currently just an idea/partially implemented.
3. **Adaptive anomaly detection**: Flag statistically unusual transactions per agent even if within hard limits.
4. **Agent trust score**: Decaying reputation score per agent based on historical violation rate.

### Explicitly not planned
- Redis, n8n, Kubernetes/Kafka, GitHub Actions (CI/CD deleted for simplicity), Decision Narration, Dry Runs.

---

## Known Issues (open, not resolved)
- **Auth "Failed to fetch"**: Account creation and login throw fetch errors (likely CORS or base URL issues).
- **Burst detection reliability**: Simulator fires too fast concurrently causing a race condition in the policy engine.

---

## Finalization Instruction
**When project is finalized (open-source MVP ready): remove all artifacts and mentions of Codestreet/AmEx from the codebase and replace with [RazorPay Hackathon Name] placeholders.** This includes:
- References in context.md, PRODUCT.md, DESIGN.md, presentation/ files
- Hackathon-specific language in comments, docs, and UI copy
- Repository name/origin references if different from final name