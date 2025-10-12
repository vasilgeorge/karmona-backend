-- Update mood check constraint to match backend schema
-- Run this in Supabase SQL Editor

-- Drop the old constraint
ALTER TABLE public.daily_reports 
DROP CONSTRAINT IF EXISTS daily_reports_mood_check;

-- Add the new constraint with correct mood values
ALTER TABLE public.daily_reports 
ADD CONSTRAINT daily_reports_mood_check 
CHECK (mood IN ('sad', 'neutral', 'good', 'great'));

