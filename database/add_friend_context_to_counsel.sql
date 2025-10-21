-- Add friend context to cosmic_counsel table
-- This allows us to show which person a question was about in the UI

ALTER TABLE public.cosmic_counsel 
ADD COLUMN IF NOT EXISTS friend_id UUID REFERENCES public.friends(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS friend_nickname TEXT,
ADD COLUMN IF NOT EXISTS friend_sun_sign TEXT,
ADD COLUMN IF NOT EXISTS friend_moon_sign TEXT;

-- Index for friend-related queries
CREATE INDEX IF NOT EXISTS idx_cosmic_counsel_friend 
ON public.cosmic_counsel(friend_id);

-- Comments
COMMENT ON COLUMN public.cosmic_counsel.friend_id IS 'ID of friend this question was about (null = about user)';
COMMENT ON COLUMN public.cosmic_counsel.friend_nickname IS 'Friend nickname at time of question';
COMMENT ON COLUMN public.cosmic_counsel.friend_sun_sign IS 'Friend sun sign at time of question';
COMMENT ON COLUMN public.cosmic_counsel.friend_moon_sign IS 'Friend moon sign at time of question';
