---
marp: true
theme: default
paginate: false
class: invert
style: |
  section {
    background-color: #09090b;
    background-image: radial-gradient(circle at 0% 100%, rgba(240, 180, 41, 0.08) 0%, transparent 50%);
    color: #f4f4f5;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    font-size: 26px; /* keeping text under 28px */
  }
  section::before {
    content: '';
    position: absolute;
    top: 50%;
    left: 0;
    width: 500px;
    height: 500px;
    background-image: 
      linear-gradient(rgba(240, 180, 41, 0.12) 1px, transparent 1px),
      linear-gradient(90deg, rgba(240, 180, 41, 0.12) 1px, transparent 1px);
    background-size: 30px 30px;
    transform: translateY(-50%);
    pointer-events: none;
    z-index: 0;
  }
  img {
    position: absolute;
    right: 40px;
    top: 48%;
    transform: translateY(-50%);
    width: 54%;
    height: auto;
    max-height: 75%;
    border: 4px solid #f0b429;
    border-radius: 4px;
    box-shadow: none;
    display: block;
  }
  .annotation {
    position: absolute;
    right: 40px;
    bottom: 30px;
    width: 54%;
    text-align: center;
    color: #f0b429;
    font-size: 20px;
    font-weight: 600;
  }
  section:has(img) h2, section:has(img) p, section:has(img) ul {
    max-width: 38%;
  }
  section.shift-left {
    padding-left: 40px;
  }
  section.shift-left h2, section.shift-left p, section.shift-left ul {
    max-width: 40%;
  }
  .flowchart {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    margin-top: 10px;
    margin-bottom: 15px;
    width: 100%;
  }
  .flow-step {
    background: rgba(240, 180, 41, 0.12);
    border: 2px solid rgba(240, 180, 41, 0.5);
    border-radius: 8px;
    padding: 8px 16px;
    text-align: center;
    width: 90%;
    max-width: 750px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
  }
  .flow-step strong {
    color: #f0b429;
    font-size: 20px;
  }
  .flow-step small {
    display: block;
    color: #a1a1aa;
    font-size: 14px;
    margin-top: 2px;
  }
  .flow-arrow {
    color: #f0b429;
    font-size: 18px;
    font-weight: bold;
    height: 14px;
    line-height: 14px;
  }
  .policy-steps {
    display: flex;
    justify-content: center;
    gap: 8px;
    margin-top: 4px;
    font-size: 14px;
    font-family: 'JetBrains Mono', monospace;
  }
  .policy-substep {
    background: rgba(240, 180, 41, 0.18);
    border: 1px solid rgba(240, 180, 41, 0.8);
    border-radius: 4px;
    padding: 1px 6px;
    color: #f4f4f5;
  }
  .policy-arrow {
    color: #f0b429;
  }
  h1, h2 {
    color: #f4f4f5;
  }
  strong {
    color: #f0b429;
  }
  code, .mono {
    font-family: 'JetBrains Mono', monospace;
    color: #a1a1aa;
  }
  section.title {
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
  }
---

<!-- _class: title -->

# Nexus

### A real-time governance layer for autonomous financial agents

**Theme 5 — Governance Layer for Financial Agents**
Codestreet 2026 · Solo build

---

## The Problem

Autonomous AI agents are starting to handle payments and servicing in finance.

There's no standard way to keep them in check:

- No granular permissions
- No real spend enforcement
- No way to instantly shut down a misbehaving fleet
- No audit trail that would hold up to a regulator

A single compromised or malfunctioning agent could rack up unauthorized transactions faster than any human would notice.

---

## The Solution

**Nexus** sits between an agent and the transaction it's trying to make.

Every request is evaluated against policy before it's allowed through.
An operator can kill the entire fleet's ability to transact with one action.

```
Agent Fleet → Policy Engine → Event Log (Postgres) → WebSocket → Dashboard
```

---

## Two-Tier Spend Cap Enforcement

Every agent has a spend cap.

- **90% of cap** → transaction allowed, but **flagged**
- **100% of cap** → transaction **denied outright**

You see risk building *before* it becomes a violation not a single hard wall with no warning.

![neon](List1.jpg)
<div class="annotation">Notice the 90% flagged transaction warning state</div>

---

## Scope Enforcement & Burst Detection

**Scope:** each agent is locked to one category. A Grocery Agent can't quietly book flights attempts outside scope are denied and logged.

**Burst detection:** abnormally fast transaction volume from one agent is caught and denied even if individual amounts look fine.

![neon](List2_BurstDenial.jpg)
<div class="annotation">The system caught and denied the abnormal burst sequence instantly</div>

---

## The Kill Switch

One control halts every agent, instantly, fleet-wide.

The halt itself is written to the audit log as its own permanent event not a flag that could be quietly flipped back. There's always a record of exactly when it was triggered.

![neon](List3_KillSwitch.jpg)
<div class="annotation">Fleet-wide halt triggered , no agents can transact</div>

---

## Immutable, Exportable Audit Trail

Every transaction attempt — allowed, denied, or flagged is permanently logged with a timestamped reason.

Exportable as CSV for compliance review.

![neon](List1.jpg)
<div class="annotation">Immutable log of all ALLOWED, DENIED, and FLAGGED events</div>

---

## Design Choice: Rules Aren't Runtime-Editable

Policy rules live in a config file, loaded once at startup.

**There is no API to change them while the system is running.**

A governance layer that can rewrite its own rules on the fly isn't really governance: this closes off a real tampering/insider-risk surface that a live-editable admin panel would leave wide open.

---

## Proving Agent-Agnosticism

Most of the fleet runs on scripted, deterministic transactions.

**One agent — Travel Agent — is driven by a real local LLM** (Qwen2.5:3b, via Ollama, fully local, no API cost, no network dependency).

It generates its own transaction requests and goes through the **exact same evaluation endpoint** as every scripted agent. No special-case handling.

---
<!-- _class: shift-left -->

## What the LLM Agent Has Already Done

- Attempted genuine off-scope and overspend transactions — not scripted, the model chose them on its own and was correctly denied
- Returned malformed output (bad JSON, markdown-wrapped) — denied and logged as its own distinct failure type, not silently retried or "fixed"


![neon](List1.jpg)
<div class="annotation">Genuine LLM agent evaluated by the exact same policy engine</div>

---

## Architecture

<div class="flowchart">
  <div class="flow-step">
    <strong>Agent Fleet</strong>
    <small>Mostly simulated, one real local LLM agent (Travel Agent)</small>
  </div>
  <div class="flow-arrow">▼</div>
  <div class="flow-step">
    <strong>Policy Engine</strong>
    <div class="policy-steps">
      <span class="policy-substep">kill_switch</span>
      <span class="policy-arrow">➔</span>
      <span class="policy-substep">scope_check</span>
      <span class="policy-arrow">➔</span>
      <span class="policy-substep">spend_cap</span>
      <span class="policy-arrow">➔</span>
      <span class="policy-substep">burst_detection</span>
    </div>
    <small>First deny wins — a flagged status does not stop execution</small>
  </div>
  <div class="flow-arrow">▼</div>
  <div class="flow-step">
    <strong>Event Log</strong>
    <small>Postgres database (append-only architecture for audit readiness)</small>
  </div>
  <div class="flow-arrow">▼</div>
  <div class="flow-step">
    <strong>WebSocket Broadcast ➔ Real-Time Dashboard</strong>
  </div>
</div>

**Stack:** FastAPI (async) · PostgreSQL · WebSockets (server-push) · React/Vite · YAML config · Ollama (local LLM)

---
## Success Metrics

- **41 transactions evaluated** in latest test session — zero gaps in the audit trail: every transaction has a timestamped decision & reason
- **15 real transactions generated by a local LLM agent** (not scripted) — 14 denied, 1 allowed
- **14 of those were genuine policy violations the LLM attempted on its own** — not from the hardcoded injector
- **1 malformed LLM response correctly identified and denied** as its own distinct failure type, not silently retried or patched

---

## Operational Gaps & Next Steps

- **Kill switch exercised multiple times this session**, each activation/restoration permanently logged as its own audit event
- **Burst detection: currently catching roughly 50% of injected burst violations** — flagged honestly as a known reliability gap
- **Root cause under investigation** — likely a timing/race condition between rapid-fire transactions and the rate-check window
- **Top priority for next phase** — resolving this rate-check window race condition is scoped as the primary target for next development cycle

---

## Scalability

- Policy engine is stateless apart from the kill-switch read — horizontal scaling isn't a hard problem
- WebSocket layer can move to a pub/sub backbone (e.g. Redis) if agent count or dashboard viewers grow
- Config-driven rules mean new agent types are a deploy-time change with version history — not a live database mutation someone could make by accident

---

<!-- _class: title -->

## Current Status

A **working prototype** already exists — ahead of what Round 1 requires.

Live dashboard | real-time enforcement | one real local LLM agent proving the core claim

