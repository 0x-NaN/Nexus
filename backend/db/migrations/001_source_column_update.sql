-- =============================================================
-- Migration 001: Update source column to support LLM degradation tiers
-- =============================================================
-- This migration updates the transactions.source column CHECK constraint
-- to allow three values instead of two:
--   - 'sim'           : scripted/simulated agents (unchanged)
--   - 'llm-hosted'    : hosted LLM API (HuggingFace Inference, etc.)
--   - 'llm-local'     : local Ollama instance
--
-- Previous values were 'sim' and 'llm'. Existing 'llm' rows are
-- migrated to 'llm-local' since those were always local Ollama calls.
-- =============================================================

-- 1. Drop the existing CHECK constraint
ALTER TABLE transactions
  DROP CONSTRAINT IF EXISTS transactions_source_check;

-- 2. Add new CHECK constraint with three allowed values
ALTER TABLE transactions
  ADD CONSTRAINT transactions_source_check
  CHECK (source IN ('sim', 'llm-hosted', 'llm-local'));

-- 3. Migrate existing 'llm' rows to 'llm-local'
UPDATE transactions
  SET source = 'llm-local'
  WHERE source = 'llm';

-- 4. Verify the migration
SELECT source, COUNT(*) AS count
FROM transactions
GROUP BY source
ORDER BY source;