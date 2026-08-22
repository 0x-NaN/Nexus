# Nexus — Project Context
**Last updated**: August 2026
**Status**: Active refactor — original hackathon folder recovered, evolving toward an industry-level open-source MVP.

---

## What Nexus Is
A real-time governance layer for fleets of autonomous AI payment-initiating agents. Sits between any agent and the transaction it wants to execute, evaluating every request against policy before allowing it through. An operator can instantly halt the entire fleet via a kill switch. Every decision — allowed, denied, or flagged — is permanently logged with a reason and exportable as CSV.

Originally built solo for Codestreet 2026 (AmEx hackathon, Theme 5: Governance Layer for Financial Agents). Not shortlisted past Round 1 out of 15,600 registrations / 6 advancing teams. Now being refactored into a genuine open-source/small-org tool rather than a demo artifact.

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
  React Dashboard (agent cards, live audit feed, kill switch, CSV export, debug panel)
```

**Key design principle that must be preserved**: policy rules are config-defined at deploy time (YAML, loaded once at startup) and are NOT runtime-editable via any API. This is a deliberate security/governance choice — not an oversight — and should never be reversed.

---

## Tech Stack (current + planned additions)

| Layer | Current | Planned addition |
|---|---|---|
| Frontend | React + Vite | motion.dev (functional motion only — see motion-design.md) |
| API | FastAPI (Python, async) | — |
| Policy | Python (in-process) | — |
| Primary DB | PostgreSQL | — |
| Real-time | WebSockets | — |
| LLM Agent | Ollama qwen2.5:3b (local, offline) | Hosted API primary + Ollama fallback (see degradation tiers below) |
| Auth | None (single-operator, demo) | JWT/OIDC |
| Observability | None | OpenTelemetry + Prometheus + Grafana (Phase 2) |
| CI/CD | None | GitHub Actions (Phase 1) |
| Deployment | Local only | Docker Compose (documented in SETUP_AND_RUN_GUIDE.md) |
| Dev tooling | OpenCode (blind) | + Filesystem/Git/GitHub/PostgreSQL/Docker MCP |
| MCP servers (configured) | — | filesystem, git (@cyanheads/git-mcp-server), github, postgres (@yawlabs/postgres-mcp), docker |

---

**MCP Setup Note**: All 5 MCPs configured in `~/.config/opencode/opencode.json` and verified connected via `opencode mcp list`.

**PPT/Deck Reminder**: When creating or updating presentation slides/decks, use **Gemini Notebook** (not the local-slide-architect MCP) for generating content — then use local-slide-architect only for final formatting/export if needed.

---

## LLM Agent Degradation Tiers (new direction — replaces offline-only approach)
Travel Agent (the real LLM-driven agent) now uses a tiered approach rather than local-only:

1. **Primary**: hosted LLM API (e.g. HuggingFace Inference or similar — use API key from environment, best model quality and speed)
2. **Fallback**: local Ollama (qwen2.5:3b) — kicks in if the hosted API call fails, times out, or returns a non-200
3. **Last resort**: scripted deterministic generator (same as the other 4 agents) — if even Ollama is unavailable; system stays fully functional, just loses the real LLM proof point for that session

Graceful degradation: the policy engine doesn't care which tier generated the request — it evaluates identically regardless of source. The source field in the DB/UI should reflect `llm-hosted`, `llm-local`, or `sim` so the audit trail is accurate about what actually generated each transaction.

---

## Planned Additions (prioritized)

### Phase 1 — alongside this refactor
- [ ] Auth (JWT/OIDC) — real multi-user support
- [ ] GitHub Actions CI/CD — lint/test on push
- [x] MCP tooling for OpenCode (Filesystem, Git, GitHub, PostgreSQL, Docker MCPs)
- [x] LLM degradation tiers (hosted primary → Ollama fallback → scripted last resort)
- [ ] motion.dev integration (functional motion only — see motion-design.md)

### Phase 2 — after Phase 1 is stable
- [ ] Observability: OpenTelemetry, Prometheus, Grafana, structured JSON logging, health/readiness endpoints, correlation IDs

### Novelty features (parked until Phase 1+2 complete, in priority order)
1. Dry-run / policy impact simulation — replay historical transactions against a hypothetical rule change before deploying it
2. LLM-powered decision narration — local model generates plain-English explanation for each deny/flag, synthesizing multiple signals
3. Adaptive anomaly detection — flag statistically unusual transactions per agent even if within hard limits (rolling stats, no ML infra)
4. Agent trust score — decaying reputation score per agent based on historical violation rate; informational/monitoring ONLY, never auto-adjusting permissions
5. Policy version history / rollback tracking

### Explicitly not planned (with reasons — don't re-litigate these)
- **Redis**: no multi-instance problem to justify it yet; stays as documented future scaling path if needed
- **n8n**: no automation-orchestration need exists in Nexus's architecture
- **Kubernetes/Kafka/microservices**: premature at this scale

---

## Known Issues (open, not resolved)
- **Burst detection reliability (~50% catch rate, fluctuates)**: suspected timing/race condition — burst transactions may evaluate against a stale rate-check before earlier transactions in the same burst have committed. Likely fix: ensure burst injector fires transactions sequentially (awaited one-at-a-time) rather than concurrently. Should be addressed properly in this refactor, not worked around again.

---

## Files to Keep Current
- `context.md` (this file) — always reflects CURRENT state; edit/update when things change, don't just append
- `changes_log.txt` — append-only historical record; log every session with timestamp, files touched, decisions, test results, NEXT line
- `PRODUCT.md` — product definition, user profiles, design principles (updated: primary user is now small-org operators, not hackathon judges)
- `DESIGN.md` — design system spec (known discrepancy: originally specced purple accent, actual implementation uses amber/gold; update to match reality during this refactor)
- `motion-design.md` — Motion policy (functional only)
- `SETUP_AND_RUN_GUIDE.md` — Local dev + production Docker deployment guide

---

## Finalization Instruction
**When project is finalized (open-source MVP ready): remove all artifacts and mentions of Codestreet/AmEx from the codebase.** This includes:
- References in context.md, PRODUCT.md, DESIGN.md, presentation/ files
- The "Codestreet Governance" branding in DESIGN.md (replace with "Nexus Governance")
- Hackathon-specific language in comments, docs, and UI copy
- Repository name/origin references if different from final name

---

## motion-design.md (create this as a new file in the project root)
Document the following decisions:
- motion.dev is added with a hard scope constraint: **functional motion only, never decorative**
- Functional = triggered by a real data change or user action: new audit trail entry slide-in, spend-meter width + color transitions, kill-switch glow/color/agent opacity change on fleet halt, flagged/denied badge appearance
- Not allowed even with the library available: page-entrance orchestration sequences, loading spinners in content areas, parallax, any animation that plays without a real trigger
- This preserves the "authority through restraint" design principle from DESIGN.md while allowing motion.dev for transitions where it adds genuine functional clarity
