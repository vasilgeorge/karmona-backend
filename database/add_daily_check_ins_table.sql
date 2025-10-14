-- Daily Check-Ins Table
-- Stores user's daily wellness data to enrich all AI-generated content

CREATE TABLE IF NOT EXISTS public.daily_check_ins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    
    -- Core wellness metrics
    mood TEXT NOT NULL,                    -- 'great', 'good', 'okay', 'low', 'struggling'
    energy_level INTEGER NOT NULL,         -- 1-10 scale
    sleep_quality TEXT NOT NULL,           -- 'excellent', 'good', 'fair', 'poor', 'terrible'
    sleep_hours DECIMAL(3,1),              -- e.g., 7.5 hours
    
    -- Biological factors
    on_menstrual_cycle BOOLEAN,            -- NULL if N/A, true/false if answered
    cycle_phase TEXT,                      -- 'menstruation', 'follicular', 'ovulation', 'luteal', NULL
    
    -- Emotional state
    feelings TEXT,                         -- Free text: "anxious", "excited", "calm", etc.
    challenges TEXT,                       -- Free text: what's weighing on them
    gratitude TEXT,                        -- Free text: what they're grateful for
    
    -- Additional context
    notes TEXT,                            -- Any other notes
    
    check_in_date DATE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Ensure one check-in per day per user
    UNIQUE(user_id, check_in_date)
);

-- Index for fast retrieval
CREATE INDEX IF NOT EXISTS idx_daily_check_ins_user_date 
ON public.daily_check_ins(user_id, check_in_date DESC);

-- RLS
ALTER TABLE public.daily_check_ins ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow all operations on daily_check_ins"
ON public.daily_check_ins FOR ALL USING (true);

