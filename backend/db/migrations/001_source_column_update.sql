-- =============================================================
-- Migration 001: Update source column to support LLM degradation tiers
-- =============================================================
-- This migration handles data migration for the source column.
-- The column and CHECK constraint are now defined in schema.sql.
-- This script only migrates existing 'llm' rows to 'llm-local'.
-- =============================================================

-- Migrate existing 'llm' rows to 'llm-local' (for any pre-existing data)
UPDATE transactions
  SET source = 'llm-local'
  WHERE source = 'llm';

-- Verify the migration
SELECT source, COUNT(*) AS count
FROM transactions
GROUP BY source
ORDER BY source;