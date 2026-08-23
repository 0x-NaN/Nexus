-- =============================================================
-- Kill Switch | Codestreet 2026
-- DB Schema — schema.sql
-- Run this first, then seed.sql
-- =============================================================

-- Clean slate (for dev resets)
DROP TABLE IF EXISTS transactions CASCADE;
DROP TABLE IF EXISTS kill_switch_events CASCADE;
DROP TABLE IF EXISTS agents CASCADE;

-- =============================================================
-- 1. agents
-- Reference table. Seeded from config/agents.yaml at startup.
-- NOT writable via API after startup — read-only from the
-- application's perspective post-seed.
-- =============================================================
CREATE TABLE agents (
  id           VARCHAR(50)    PRIMARY KEY,
  name         VARCHAR(100)   NOT NULL,
  category     VARCHAR(50)    NOT NULL,
  spend_cap    NUMERIC(10, 2) NOT NULL CHECK (spend_cap > 0),
  rate_limit   INTEGER        CHECK (rate_limit IS NULL OR rate_limit > 0),
  -- rate_limit: max transactions per minute; NULL = no burst limit for this agent
  normal_range_min NUMERIC(10, 2) NOT NULL,
  normal_range_max NUMERIC(10, 2) NOT NULL,
  CHECK (normal_range_min < normal_range_max),
  CHECK (normal_range_max <= spend_cap)
);

-- =============================================================
-- 2. transactions
-- Core event log. APPEND-ONLY — never update, never delete.
-- Every transaction evaluated by the policy engine lands here,
-- regardless of outcome.
-- =============================================================
CREATE TABLE transactions (
  id                      VARCHAR(60)    PRIMARY KEY,
  -- Format: txn_<YYYYMMDD>_<HHMMSS>_<6-char random>
  -- e.g. txn_20260719_074500_a3f8c1

  agent_id                VARCHAR(50)    NOT NULL REFERENCES agents(id),
  amount                  NUMERIC(10, 2) NOT NULL CHECK (amount > 0),
  category                VARCHAR(50)    NOT NULL,

  timestamp               TIMESTAMPTZ    NOT NULL DEFAULT NOW(),

  decision                VARCHAR(10)    NOT NULL
                            CHECK (decision IN ('allowed', 'denied', 'flagged')),

  reason                  VARCHAR(100),
  -- NULL when decision = 'allowed'
  -- Allowed values:
  --   'exceeds_spend_cap'     — amount would push total over cap
  --   'off_scope_category'    — transaction.category != agent.category
  --   'burst_limit_exceeded'  — tx count in window > agent.rate_limit
  --   'kill_switch_active'    — global kill switch is in 'killed' state

  is_injected_misbehavior BOOLEAN        NOT NULL DEFAULT FALSE,
  -- TRUE when simulator deliberately injected this transaction as a test case

  misbehavior_type        VARCHAR(20)
                            CHECK (misbehavior_type IS NULL OR
                                   misbehavior_type IN ('overspend', 'off_scope', 'burst')),
  -- Informational only. Policy engine ignores this field during evaluation.
  -- NULL for normal noise transactions.

  source                  VARCHAR(20)    NOT NULL DEFAULT 'sim'
                            CHECK (source IN ('sim', 'llm-hosted', 'llm-local')),
  -- Source of transaction: 'sim' (scripted), 'llm-hosted' (hosted API), 'llm-local' (local Ollama)

  CONSTRAINT reason_required_on_deny_flag
    CHECK (
      (decision = 'allowed' AND reason IS NULL)
      OR
      (decision IN ('denied', 'flagged') AND reason IS NOT NULL)
    )
);

-- Index: common query patterns
CREATE INDEX idx_transactions_agent_id   ON transactions (agent_id);
CREATE INDEX idx_transactions_timestamp  ON transactions (timestamp DESC);
CREATE INDEX idx_transactions_decision   ON transactions (decision);
CREATE INDEX idx_transactions_injected   ON transactions (is_injected_misbehavior)
  WHERE is_injected_misbehavior = TRUE;

-- Composite: agent spend total (most common query — sum per agent)
CREATE INDEX idx_transactions_agent_decision
  ON transactions (agent_id, decision);

-- =============================================================
-- 3. kill_switch_events
-- Dual-purpose: current-state source AND full audit trail.
-- Current state = most recent row by timestamp.
-- APPEND-ONLY — each flip creates a new row, never mutates old ones.
-- =============================================================
CREATE TABLE kill_switch_events (
  id            SERIAL         PRIMARY KEY,
  state         VARCHAR(10)    NOT NULL CHECK (state IN ('active', 'killed')),
  timestamp     TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
  triggered_by  VARCHAR(50)    NOT NULL DEFAULT 'manual'
  -- 'manual'          — dashboard user action
  -- 'system_startup'  — initial seed row
);

-- Index: current-state lookup (always just MAX(timestamp) or ORDER BY timestamp DESC LIMIT 1)
CREATE INDEX idx_kill_switch_timestamp ON kill_switch_events (timestamp DESC);

-- =============================================================
-- Helper view: current spend totals per agent
-- Used by GET /agents and GET /agents/{id}
-- Only counts 'allowed' + 'flagged' decisions (denied = no money moved)
-- =============================================================
CREATE OR REPLACE VIEW agent_spend_totals AS
SELECT
  a.id          AS agent_id,
  a.name,
  a.category,
  a.spend_cap,
  a.rate_limit,
  COALESCE(SUM(t.amount) FILTER (WHERE t.decision IN ('allowed', 'flagged')), 0.00)
                AS spend_total,
  ROUND(
    COALESCE(SUM(t.amount) FILTER (WHERE t.decision IN ('allowed', 'flagged')), 0.00)
    / a.spend_cap * 100,
  2)            AS spend_pct
FROM agents a
LEFT JOIN transactions t ON t.agent_id = a.id
GROUP BY a.id, a.name, a.category, a.spend_cap, a.rate_limit;

-- =============================================================
-- Helper view: current kill switch state
-- Eliminates the ORDER BY / LIMIT 1 pattern from application code
-- =============================================================
CREATE OR REPLACE VIEW current_kill_switch AS
SELECT state, timestamp, triggered_by
FROM kill_switch_events
ORDER BY timestamp DESC
LIMIT 1;

-- =============================================================
-- Helper view: recent transaction rate per agent (burst detection)
-- Counts transactions per agent in the last 60 seconds
-- =============================================================
CREATE OR REPLACE VIEW agent_recent_tx_rate AS
SELECT
  agent_id,
  COUNT(*) AS tx_count_last_60s
FROM transactions
WHERE timestamp >= NOW() - INTERVAL '60 seconds'
GROUP BY agent_id;
