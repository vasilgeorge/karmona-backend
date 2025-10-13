-- Add weekly forecasts table
-- Run this in Supabase SQL Editor

CREATE TABLE IF NOT EXISTS public.weekly_forecasts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    sun_sign TEXT NOT NULL,
    week_start DATE NOT NULL,
    week_end DATE NOT NULL,
    forecast TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, week_start)
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_weekly_forecasts_user_week 
ON public.weekly_forecasts(user_id, week_start DESC);

-- Enable RLS
ALTER TABLE public.weekly_forecasts ENABLE ROW LEVEL SECURITY;

-- Allow all operations for now (add proper auth policies later)
CREATE POLICY "Allow all operations on weekly_forecasts" 
ON public.weekly_forecasts FOR ALL USING (true);

