-- Add Stripe subscription columns to users table

ALTER TABLE public.users 
ADD COLUMN IF NOT EXISTS stripe_customer_id TEXT UNIQUE,
ADD COLUMN IF NOT EXISTS subscription_status TEXT DEFAULT 'free',
ADD COLUMN IF NOT EXISTS subscription_tier TEXT DEFAULT 'free',
ADD COLUMN IF NOT EXISTS stripe_subscription_id TEXT,
ADD COLUMN IF NOT EXISTS subscription_period_end TIMESTAMPTZ;

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_stripe_customer 
ON public.users(stripe_customer_id);

CREATE INDEX IF NOT EXISTS idx_users_subscription_status 
ON public.users(subscription_status);

COMMENT ON COLUMN public.users.subscription_status IS 'Stripe subscription status: free, active, past_due, canceled, incomplete';
COMMENT ON COLUMN public.users.subscription_tier IS 'Subscription tier: free, premium';

