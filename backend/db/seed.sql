-- =============================================================
-- Kill Switch | [RazorPay Hackathon 2026]
-- DB Seed — seed.sql
-- Run AFTER schema.sql
-- Seeds the agents table from config/agents.yaml values.
-- Also inserts the system_startup kill_switch row.
-- =============================================================

-- NOTE: These values mirror config/agents.yaml exactly.
-- If agents.yaml is changed, update this file to match.
-- The application also re-seeds from YAML at startup (upsert),
-- but this file exists for a clean manual DB setup.

-- =============================================================
-- agents
-- =============================================================
INSERT INTO agents (id, name, category, spend_cap, rate_limit, normal_range_min, normal_range_max)
VALUES
  ('agent_001', 'Grocery Agent',         'grocery',      500.00,  10,   15.00,  120.00),
  ('agent_002', 'Subscription Agent',    'subscription', 200.00,  NULL,  9.00,   50.00),
  ('agent_003', 'Travel Agent',          'travel',      1500.00,   5,   80.00,  600.00),
  ('agent_004', 'Dining Agent',          'dining',       300.00,   8,   20.00,   90.00),
  ('agent_005', 'Office Supplies Agent', 'office',       250.00,  NULL, 10.00,   80.00)
ON CONFLICT (id) DO UPDATE
  SET
    name             = EXCLUDED.name,
    category         = EXCLUDED.category,
    spend_cap        = EXCLUDED.spend_cap,
    rate_limit       = EXCLUDED.rate_limit,
    normal_range_min = EXCLUDED.normal_range_min,
    normal_range_max = EXCLUDED.normal_range_max;

-- =============================================================
-- kill_switch_events — initial state
-- =============================================================
-- Only insert if no rows exist yet (idempotent)
INSERT INTO kill_switch_events (state, triggered_by)
SELECT 'active', 'system_startup'
WHERE NOT EXISTS (SELECT 1 FROM kill_switch_events);
