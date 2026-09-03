-- =========================================================
-- Member 3: Worker Stability & Risk Scoring Engine Schema
-- Supabase / PostgreSQL DDL (100% Compatible)
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
    worker_id UUID NOT NULL,
    stability_score DOUBLE PRECISION NOT NULL CHECK (stability_score >= 0.0 AND stability_score <= 100.0),
    risk_tier risk_tier_enum NOT NULL,
    metrics_breakdown JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- 3. Create indexes for rapid lookup by worker_id and created_at
CREATE INDEX IF NOT EXISTS idx_risk_scores_worker_id ON public.risk_scores (worker_id);
CREATE INDEX IF NOT EXISTS idx_risk_scores_worker_created ON public.risk_scores (worker_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_risk_scores_risk_tier ON public.risk_scores (risk_tier);

-- 4. Enable Row Level Security (RLS)
ALTER TABLE public.risk_scores ENABLE ROW LEVEL SECURITY;

-- 5. Policies: Drop first if existing to prevent syntax errors, then create
DROP POLICY IF EXISTS "Allow service role and authenticated full access" ON public.risk_scores;

CREATE POLICY "Allow service role and authenticated full access" 
ON public.risk_scores 
FOR ALL 
USING (true) 
WITH CHECK (true);
