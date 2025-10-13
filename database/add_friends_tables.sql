-- Add friends and compatibility tables
-- Run this in Supabase SQL Editor

-- Friends table
CREATE TABLE IF NOT EXISTS public.friends (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    nickname TEXT NOT NULL,
    sun_sign TEXT NOT NULL,
    moon_sign TEXT,
    birth_location TEXT,
    current_location TEXT,
    age INTEGER,
    relationship_type TEXT NOT NULL CHECK (
        relationship_type IN ('friend', 'romantic', 'professional', 'family', 'acquaintance', 'mentor')
    ),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Compatibility reports table (cached daily)
CREATE TABLE IF NOT EXISTS public.compatibility_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    friend_id UUID NOT NULL REFERENCES public.friends(id) ON DELETE CASCADE,
    report TEXT NOT NULL,
    relationship_type TEXT NOT NULL,
    generated_date DATE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(friend_id, generated_date)  -- One report per friend per day
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_friends_user_id ON public.friends(user_id);
CREATE INDEX IF NOT EXISTS idx_compatibility_user_friend ON public.compatibility_reports(user_id, friend_id);
CREATE INDEX IF NOT EXISTS idx_compatibility_date ON public.compatibility_reports(generated_date DESC);

-- Enable RLS
ALTER TABLE public.friends ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.compatibility_reports ENABLE ROW LEVEL SECURITY;

-- Policies
CREATE POLICY "Allow all operations on friends" 
ON public.friends FOR ALL USING (true);

CREATE POLICY "Allow all operations on compatibility_reports" 
ON public.compatibility_reports FOR ALL USING (true);

-- Update trigger for friends
CREATE TRIGGER update_friends_updated_at BEFORE UPDATE ON public.friends
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

