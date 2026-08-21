# Kill Switch — API Contract
**Version:** 0.1 | **Drafted:** 2026-07-19 | **Status:** Locked for implementation

---

## Overview

Two internal services share this contract:
- **Policy Engine** (FastAPI) — the authoritative backend. All state lives here.
- **Transaction Simulator** — calls the Policy Engine just like a real agent would. Separate internal contract section below.

The Dashboard (React) talks only to the Policy Engine (REST + WebSocket).  
The Simulator talks only to the Policy Engine (REST, internal).

---

## Base URL
```
http://localhost:8000
```
WebSocket:
```
ws://localhost:8000/ws
```

---

## 1. Agents

> Reference data. Seeded from config at startup. No write endpoints exposed — agents are not runtime-mutable.

### `GET /agents`
Returns the full agent pool with current spend totals computed from the transaction log.

**Response `200`:**
```json
[
  {
    "id": "agent_001",
    "name": "Grocery Agent",
    "category": "grocery",
    "spend_cap": 500.00,
    "rate_limit": 10,
    "spend_total": 312.45,
    "status": "active"
  }
]
```
- `spend_total` — sum of `amount` for all `allowed` + `flagged` transactions this session (or rolling window — TBD at impl)
- `status` — `"active"` | `"halted"` (halted when kill switch is `killed`)
- `rate_limit` — max transactions per minute; `null` if not configured for that agent

---

### `GET /agents/{agent_id}`
Single agent detail. Same shape as above, plus last 10 transactions inline.

**Response `200`:**
```json
{
  "id": "agent_001",
  "name": "Grocery Agent",
  "category": "grocery",
  "spend_cap": 500.00,
  "rate_limit": 10,
  "spend_total": 312.45,
  "status": "active",
  "recent_transactions": []
}
```

**Response `404`:** `{ "detail": "Agent not found" }`

---

## 2. Policy Engine — Transaction Evaluation

> Core endpoint. Called by the Simulator (and would be called by real agents in a production system). The single chokepoint through which all transactions pass.

### `POST /transaction/evaluate`
Submit a transaction for policy evaluation. Engine checks kill-switch first, then spend cap, then scope, then rate limit. Decision is written to event log before returning.

**Request body:**
```json
{
  "agent_id": "agent_001",
  "amount": 84.50,
  "category": "grocery",
  "is_injected_misbehavior": false,
  "misbehavior_type": null
}
```
- `is_injected_misbehavior` — boolean; simulator sets `true` when this tx was deliberately injected
- `misbehavior_type` — `null` | `"overspend"` | `"off_scope"` | `"burst"` — informational, logged as-is; policy engine does NOT alter its logic based on this (it evaluates rules independently)

**Response `200`:**
```json
{
  "transaction_id": "txn_20260719_001",
  "agent_id": "agent_001",
  "amount": 84.50,
  "category": "grocery",
  "timestamp": "2026-07-19T07:40:00Z",
  "decision": "allowed",
  "reason": null,
  "is_injected_misbehavior": false,
  "misbehavior_type": null
}
```

**`decision` enum values:**
| Value | Meaning |
|-------|---------|
| `allowed` | Transaction passes all policy checks |
| `flagged` | Suspicious but not hard-blocked (e.g. approaching cap) — treat as allowed with warning |
| `denied` | Transaction blocked by policy |

**`reason` values (when `denied` or `flagged`):**
| Reason string | Trigger |
|---------------|---------|
| `"exceeds_spend_cap"` | `spend_total + amount > spend_cap` |
| `"off_scope_category"` | `transaction.category != agent.category` |
| `"burst_limit_exceeded"` | Transactions in last 60s > `rate_limit` |
| `"kill_switch_active"` | Global kill switch is in `killed` state |

**Response `404`:** Agent not found
**Response `422`:** Validation error on request body

---

## 3. Event Log — Transactions

### `GET /transactions`
Full audit log. Supports filtering and pagination.

**Query params:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `agent_id` | string | — | Filter by agent |
| `decision` | string | — | `allowed` / `denied` / `flagged` |
| `is_injected` | bool | — | Filter to only injected misbehaviors |
| `limit` | int | 100 | Max records returned |
| `offset` | int | 0 | Pagination offset |
| `since` | ISO datetime | — | Filter to transactions after this timestamp |

**Response `200`:**
```json
{
  "total": 342,
  "limit": 100,
  "offset": 0,
  "transactions": [
    {
      "id": "txn_20260719_001",
      "agent_id": "agent_001",
      "agent_name": "Grocery Agent",
      "amount": 84.50,
      "category": "grocery",
      "timestamp": "2026-07-19T07:40:00Z",
      "decision": "denied",
      "reason": "exceeds_spend_cap",
      "is_injected_misbehavior": true,
      "misbehavior_type": "overspend"
    }
  ]
}
```

---

### `GET /transactions/export`
Export the full log (or a filtered subset using the same query params as above).

**Query params:** Same as `GET /transactions` (no pagination — returns all matching)
**Additional param:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `format` | string | `json` | `json` or `csv` |

**Response `200`:** JSON array or CSV file download (`Content-Disposition: attachment; filename="audit_log.csv"`)

---

## 4. Kill Switch

### `GET /kill-switch`
Returns current kill-switch state (derived from most recent row in `kill_switch_events`).

**Response `200`:**
```json
{
  "state": "active",
  "last_changed": "2026-07-19T07:30:00Z",
  "triggered_by": "manual"
}
```
- `state` — `"active"` | `"killed"`

---

### `POST /kill-switch`
Flip the kill switch. Creates a new row in `kill_switch_events`. Toggle semantics (new state = opposite of current).

**Request body:**
```json
{
  "triggered_by": "manual"
}
```

**Response `200`:** Same shape as `GET /kill-switch`, reflecting new state.

---

### `GET /kill-switch/history`
Full audit trail of every kill-switch state change.

**Response `200`:**
```json
[
  {
    "id": 1,
    "state": "killed",
    "timestamp": "2026-07-19T07:45:00Z",
    "triggered_by": "manual"
  },
  {
    "id": 2,
    "state": "active",
    "timestamp": "2026-07-19T07:46:30Z",
    "triggered_by": "manual"
  }
]
```

---

## 5. Simulator Control (Internal / Debug)

> In the demo, the hidden debug panel in the frontend calls these directly.

### `GET /simulator/status`

**Response `200`:**
```json
{
  "running": true,
  "normal_interval_ms": 1500,
  "injection_probability": 0.15,
  "last_injection": {
    "agent_id": "agent_003",
    "misbehavior_type": "overspend",
    "timestamp": "2026-07-19T07:44:00Z"
  }
}
```

---

### `POST /simulator/start`
Start the simulator.

**Request body (optional overrides):**
```json
{
  "normal_interval_ms": 1500,
  "injection_probability": 0.15
}
```
**Response `200`:** `{ "running": true }`

---

### `POST /simulator/stop`

**Response `200`:** `{ "running": false }`

---

### `POST /simulator/inject`
**Manual override — what the debug panel button calls.**

**Request body:**
```json
{
  "agent_id": null,
  "misbehavior_type": "overspend"
}
```
- `agent_id` — `null` = pick random agent; or specify an agent ID
- `misbehavior_type` — `"overspend"` | `"off_scope"` | `"burst"` | `"random"`

**Response `200`:** Same shape as `POST /transaction/evaluate` response.

---

## 6. WebSocket — Real-Time Feed

### `WS /ws`
Single persistent connection. Dashboard connects once; server pushes all events.

### Message types pushed by server:

**`transaction_event`** — after every transaction evaluated:
```json
{
  "type": "transaction_event",
  "data": {
    "id": "txn_20260719_001",
    "agent_id": "agent_001",
    "agent_name": "Grocery Agent",
    "amount": 84.50,
    "category": "grocery",
    "timestamp": "2026-07-19T07:40:00Z",
    "decision": "denied",
    "reason": "exceeds_spend_cap",
    "is_injected_misbehavior": true,
    "misbehavior_type": "overspend"
  }
}
```

**`kill_switch_event`** — whenever kill-switch state changes:
```json
{
  "type": "kill_switch_event",
  "data": {
    "state": "killed",
    "timestamp": "2026-07-19T07:45:00Z",
    "triggered_by": "manual"
  }
}
```

**`agent_update`** — after any transaction changes an agent's spend total (so meters update without polling):
```json
{
  "type": "agent_update",
  "data": {
    "agent_id": "agent_001",
    "spend_total": 396.95,
    "status": "active"
  }
}
```

Client → Server: **None**. WebSocket is server-push only. Dashboard sends actions via REST.

---

## 7. Simulator Internal Contract

> Not an HTTP API — internal design spec for the simulator process.

### Agent Pool (`config/agents.yaml`)
```yaml
agents:
  - id: agent_001
    name: "Grocery Agent"
    category: grocery
    spend_cap: 500.00
    rate_limit: 10
    normal_range: [15, 120]

  - id: agent_002
    name: "Subscription Agent"
    category: subscription
    spend_cap: 200.00
    rate_limit: null
    normal_range: [9, 50]

  - id: agent_003
    name: "Travel Agent"
    category: travel
    spend_cap: 1500.00
    rate_limit: 5
    normal_range: [80, 600]

  - id: agent_004
    name: "Dining Agent"
    category: dining
    spend_cap: 300.00
    rate_limit: 8
    normal_range: [20, 90]

  - id: agent_005
    name: "Office Supplies Agent"
    category: office
    spend_cap: 250.00
    rate_limit: null
    normal_range: [10, 80]
```

### Behavior Pool (hardcoded in simulator)
| Behavior | What the simulator does |
|----------|------------------------|
| `overspend` | `amount = agent.spend_cap * random(1.1, 1.5)` — guaranteed over cap |
| `off_scope` | `category` = any category other than agent's own |
| `burst` | Fire 6–10 rapid calls to `/transaction/evaluate` in ~5 seconds, all normal amounts |

### Normal Generator Logic
- Every `normal_interval_ms` (default 1500ms): pick random agent, generate amount in `normal_range`, category = agent's own, `is_injected_misbehavior = false`
- On each tick: roll `injection_probability` (default 0.15) — if hit, run misbehavior injector for this tick instead
- For `burst` misbehavior: fire N calls (random 6–10) in rapid succession before returning

---

## 8. Policy Engine Rule Config (`config/policy_rules.yaml`)

```yaml
# Loaded at startup only. NOT runtime-editable.
# Changing rules requires a restart — by design.

rules:
  spend_cap:
    enabled: true
    flag_threshold_pct: 0.90   # flag (warn) at 90% of cap
    deny_threshold_pct: 1.00   # deny at 100% of cap

  scope_check:
    enabled: true
    # transaction.category must match agent.category; deny on mismatch

  burst_detection:
    enabled: true
    window_seconds: 60
    # deny if tx count in window > agent.rate_limit (only for agents with rate_limit set)

  kill_switch:
    enabled: true
    # checked FIRST, before all other rules
    # if state = killed -> deny with reason "kill_switch_active"
```

---

## 9. DB Schema — DDL Reference

```sql
-- Agents: seeded from config at startup. Not writable via API after startup.
CREATE TABLE agents (
  id          VARCHAR(50)   PRIMARY KEY,
  name        VARCHAR(100)  NOT NULL,
  category    VARCHAR(50)   NOT NULL,
  spend_cap   NUMERIC(10,2) NOT NULL,
  rate_limit  INTEGER       -- NULL = no limit
);

-- Transactions: core event log. Append-only.
CREATE TABLE transactions (
  id                      VARCHAR(50)   PRIMARY KEY,
  agent_id                VARCHAR(50)   NOT NULL REFERENCES agents(id),
  amount                  NUMERIC(10,2) NOT NULL,
  category                VARCHAR(50)   NOT NULL,
  timestamp               TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
  decision                VARCHAR(10)   NOT NULL CHECK (decision IN ('allowed','denied','flagged')),
  reason                  VARCHAR(100),
  is_injected_misbehavior BOOLEAN       NOT NULL DEFAULT FALSE,
  misbehavior_type        VARCHAR(20)   -- NULL | 'overspend' | 'off_scope' | 'burst'
);

-- Kill switch events: current-state source AND its own audit trail.
-- Current state = most recent row by timestamp.
CREATE TABLE kill_switch_events (
  id            SERIAL      PRIMARY KEY,
  state         VARCHAR(10) NOT NULL CHECK (state IN ('active','killed')),
  timestamp     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  triggered_by  VARCHAR(50) NOT NULL DEFAULT 'manual'
);

-- Seed: system starts in 'active' state
INSERT INTO kill_switch_events (state, triggered_by) VALUES ('active', 'system_startup');
```

---

## 10. Error Response Shape

```json
{
  "detail": "Human-readable error message",
  "code": "machine_readable_error_code"
}
```

Standard HTTP codes: `200` OK, `404` Not Found, `409` Conflict, `422` Validation Error, `500` Internal Error.

---

*End of API Contract v0.1 — 2026-07-19*
