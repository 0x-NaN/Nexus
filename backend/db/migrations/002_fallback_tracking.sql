-- =============================================================
-- Kill Switch | [RazorPay Hackathon 2026]
-- Migration 002: Fallback Tracking Columns
-- Add columns to track fallback status for transactions
-- =============================================================

-- Add fallback tracking columns to transactions table
ALTER TABLE transactions 
ADD COLUMN IF NOT EXISTS fallback_status VARCHAR(20) 
    CHECK (fallback_status IS NULL OR fallback_status IN ('pending', 'resolved', 'failed')),
ADD COLUMN IF NOT EXISTS fallback_reason VARCHAR(100),
ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMPTZ;

-- Index for querying fallback transactions
CREATE INDEX IF NOT EXISTS idx_transactions_fallback_status 
ON transactions (fallback_status) 
WHERE fallback_status IS NOT NULL;

-- Add comments
COMMENT ON COLUMN transactions.fallback_status IS 'Tracks fallback state: pending (written to JSONL), resolved (replayed to PG), failed (replay failed)';
COMMENT ON COLUMN transactions.fallback_reason IS 'Reason for fallback: db_disconnected, etc.';
COMMENT ON COLUMN transactions.resolved_at IS 'Timestamp when fallback was resolved and replayed to PostgreSQL';
