-- Add cancel_at_period_end column to track pending cancellations

ALTER TABLE public.users 
ADD COLUMN IF NOT EXISTS cancel_at_period_end BOOLEAN DEFAULT false;

COMMENT ON COLUMN public.users.cancel_at_period_end IS 'True if user cancelled but subscription still active until period end';
