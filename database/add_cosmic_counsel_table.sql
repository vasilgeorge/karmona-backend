-- Cosmic Counsel Table
-- Stores user questions and AI-generated guidance

CREATE TABLE IF NOT EXISTS public.cosmic_counsel (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    
    -- Question details
    question TEXT NOT NULL,
    category TEXT,  -- 'career', 'love', 'finance', 'life_change', 'relationships', 'other'
    
    -- AI-generated answer
    answer TEXT NOT NULL,
    
    -- Context used for answer
    sun_sign TEXT NOT NULL,
    moon_sign TEXT,
    mood TEXT,  -- From daily check-in
    energy_level INTEGER,  -- From daily check-in
    
    -- Metadata
    asked_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast retrieval by user and date
CREATE INDEX IF NOT EXISTS idx_cosmic_counsel_user_date 
ON public.cosmic_counsel(user_id, asked_at DESC);

-- Index for category filtering
CREATE INDEX IF NOT EXISTS idx_cosmic_counsel_category 
ON public.cosmic_counsel(category);

-- RLS
ALTER TABLE public.cosmic_counsel ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow all operations on cosmic_counsel"
ON public.cosmic_counsel FOR ALL USING (true);

