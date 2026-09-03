-- Ensure UUID generation function is available (portable across plain Postgres)
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- =========================================================
-- 1. Work Logs Table
-- =========================================================
CREATE TABLE IF NOT EXISTS work_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    worker_id UUID NOT NULL, -- TODO: REFERENCES workers(id) once Member 1's table exists
    log_date TIMESTAMPTZ NOT NULL,
    hours_worked NUMERIC(5, 2) NOT NULL CHECK (hours_worked >= 0),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_work_logs_worker_id ON work_logs (worker_id);
CREATE INDEX IF NOT EXISTS idx_work_logs_worker_date ON work_logs (worker_id, log_date DESC);

-- =========================================================
-- 2. Earnings Table
-- =========================================================
CREATE TABLE IF NOT EXISTS earnings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    worker_id UUID NOT NULL, -- TODO: REFERENCES workers(id)
    amount NUMERIC(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'INR',
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,
    is_missing_data BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CHECK (period_end >= period_start)
);

CREATE INDEX IF NOT EXISTS idx_earnings_worker_id ON earnings (worker_id);
CREATE INDEX IF NOT EXISTS idx_earnings_worker_period ON earnings (worker_id, period_start DESC);

-- =========================================================
-- 3. Transactions Table
-- =========================================================
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'transaction_type_enum') THEN
        CREATE TYPE transaction_type_enum AS ENUM ('payout', 'deposit', 'withdrawal', 'adjustment');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'transaction_status_enum') THEN
        CREATE TYPE transaction_status_enum AS ENUM ('pending', 'completed', 'failed', 'reversed');
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    worker_id UUID NOT NULL, -- TODO: REFERENCES workers(id)
    amount NUMERIC(10, 2) NOT NULL,
    transaction_type transaction_type_enum NOT NULL,
    status transaction_status_enum NOT NULL,
    transaction_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_transactions_worker_id ON transactions (worker_id);
CREATE INDEX IF NOT EXISTS idx_transactions_worker_time ON transactions (worker_id, transaction_time DESC);

-- =========================================================
-- Member 3: Worker Stability & Risk Scoring Engine Schema
-- =========================================================

-- 1. Safely create Risk Tier Enum if it does not already exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'risk_tier_enum') THEN
        CREATE TYPE risk_tier_enum AS ENUM ('Stable', 'At Risk', 'Critical');
    END IF;
END $$;

-- 2. Create the risk_scores table
CREATE TABLE IF NOT EXISTS public.risk_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    worker_id UUID NOT NULL, -- TODO: REFERENCES workers(id)
    stability_score DOUBLE PRECISION NOT NULL CHECK (stability_score >= 0.0 AND stability_score <= 100.0),
    risk_tier risk_tier_enum NOT NULL,
    metrics_breakdown JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- 3. Indexes for rapid lookup by worker_id and created_at
CREATE INDEX IF NOT EXISTS idx_risk_scores_worker_id ON public.risk_scores (worker_id);
CREATE INDEX IF NOT EXISTS idx_risk_scores_worker_created ON public.risk_scores (worker_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_risk_scores_risk_tier ON public.risk_scores (risk_tier);

-- 4. Enable Row Level Security (RLS)
ALTER TABLE public.risk_scores ENABLE ROW LEVEL SECURITY;

-- 5. Correct policies: scoped to specific roles, not PUBLIC/anon.
-- Service role (backend jobs) gets full access.
DROP POLICY IF EXISTS "Service role full access" ON public.risk_scores;
CREATE POLICY "Service role full access"
ON public.risk_scores
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Authenticated users can only read (and only their own worker's rows,
-- once you have a way to map auth.uid() -> worker_id — placeholder shown).
DROP POLICY IF EXISTS "Authenticated read own risk score" ON public.risk_scores;
CREATE POLICY "Authenticated read own risk score"
ON public.risk_scores
FOR SELECT
TO authenticated
USING (worker_id = auth.uid()); -- adjust once worker<->auth mapping exists
ALTER TABLE earnings DISABLE ROW LEVEL SECURITY;
ALTER TABLE work_logs DISABLE ROW LEVEL SECURITY;
ALTER TABLE transactions DISABLE ROW LEVEL SECURITY;