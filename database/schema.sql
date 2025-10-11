-- Karmona Backend Database Schema
-- Run this in your Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    birthdate DATE NOT NULL,
    birth_time VARCHAR(5),  -- HH:MM format
    birth_place VARCHAR(200),
    sun_sign VARCHAR(20) NOT NULL,
    moon_sign VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Daily reports table
CREATE TABLE IF NOT EXISTS daily_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    mood VARCHAR(20) NOT NULL,  -- 'sad', 'neutral', 'good', 'great'
    actions JSONB NOT NULL,  -- Array of action strings
    karma_score INTEGER NOT NULL CHECK (karma_score >= 0 AND karma_score <= 100),
    reading TEXT NOT NULL,
    rituals JSONB NOT NULL,  -- Array of ritual strings
    note TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, date)  -- One report per user per day
);

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_daily_reports_user_id ON daily_reports(user_id);
CREATE INDEX IF NOT EXISTS idx_daily_reports_date ON daily_reports(date);
CREATE INDEX IF NOT EXISTS idx_daily_reports_user_date ON daily_reports(user_id, date DESC);

-- Updated at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to users table
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS) Policies
-- Enable RLS on tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_reports ENABLE ROW LEVEL SECURITY;

-- Users policies
-- Allow service role to do everything
CREATE POLICY "Service role has full access to users"
    ON users
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Users can read their own data
CREATE POLICY "Users can read own data"
    ON users
    FOR SELECT
    TO authenticated
    USING (auth.uid()::text = id::text);

-- Daily reports policies
-- Allow service role to do everything
CREATE POLICY "Service role has full access to daily_reports"
    ON daily_reports
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Users can read their own reports
CREATE POLICY "Users can read own reports"
    ON daily_reports
    FOR SELECT
    TO authenticated
    USING (auth.uid()::text = user_id::text);

-- Optional: Waitlist table (if shared with frontend)
CREATE TABLE IF NOT EXISTS waitlist_emails (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100),
    source VARCHAR(50) DEFAULT 'landing',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_waitlist_email ON waitlist_emails(email);

-- Comments for documentation
COMMENT ON TABLE users IS 'User profiles with birth information and astrology data';
COMMENT ON TABLE daily_reports IS 'Daily karma reflections and scores';
COMMENT ON TABLE waitlist_emails IS 'Email waitlist for pre-launch signups';

COMMENT ON COLUMN users.sun_sign IS 'Zodiac sun sign (Aries, Taurus, etc.)';
COMMENT ON COLUMN users.moon_sign IS 'Zodiac moon sign (requires birth time)';
COMMENT ON COLUMN daily_reports.karma_score IS 'Karma score from 0-100';
COMMENT ON COLUMN daily_reports.actions IS 'JSON array of action types';
COMMENT ON COLUMN daily_reports.rituals IS 'JSON array of 2 ritual suggestions';

