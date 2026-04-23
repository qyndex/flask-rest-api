-- Initial schema for Flask REST API (Supabase deployment option)
-- SQLAlchemy is the primary ORM; this file mirrors the schema for Supabase hosting.

-- Enable UUID extension (available by default in Supabase)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- Users table
-- ============================================================
CREATE TABLE IF NOT EXISTS public.users (
    id              SERIAL PRIMARY KEY,
    email           VARCHAR(255) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    full_name       VARCHAR(200) NOT NULL DEFAULT '',
    role            VARCHAR(50)  NOT NULL DEFAULT 'user',
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON public.users (email);

-- ============================================================
-- Items table
-- ============================================================
CREATE TABLE IF NOT EXISTS public.items (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(200) NOT NULL,
    description     TEXT         NOT NULL DEFAULT '',
    price           DOUBLE PRECISION NOT NULL,
    quantity        INTEGER      NOT NULL DEFAULT 0,
    category        VARCHAR(100) NOT NULL DEFAULT 'general',
    status          VARCHAR(50)  NOT NULL DEFAULT 'active',
    is_available    BOOLEAN      NOT NULL DEFAULT TRUE,
    created_by      INTEGER      REFERENCES public.users(id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_items_category ON public.items (category);
CREATE INDEX IF NOT EXISTS idx_items_status   ON public.items (status);
CREATE INDEX IF NOT EXISTS idx_items_created_by ON public.items (created_by);

-- ============================================================
-- Row-Level Security
-- ============================================================
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.items ENABLE ROW LEVEL SECURITY;

-- Users can read their own profile
CREATE POLICY users_select_own ON public.users
    FOR SELECT USING (auth.uid()::text = id::text);

-- Users can update their own profile
CREATE POLICY users_update_own ON public.users
    FOR UPDATE USING (auth.uid()::text = id::text);

-- Anyone can read items
CREATE POLICY items_select_all ON public.items
    FOR SELECT USING (true);

-- Authenticated users can insert items (owned by them)
CREATE POLICY items_insert_own ON public.items
    FOR INSERT WITH CHECK (auth.uid()::text = created_by::text);

-- Users can only update their own items
CREATE POLICY items_update_own ON public.items
    FOR UPDATE USING (auth.uid()::text = created_by::text);

-- Users can only delete their own items
CREATE POLICY items_delete_own ON public.items
    FOR DELETE USING (auth.uid()::text = created_by::text);

-- ============================================================
-- Trigger: auto-update updated_at on items
-- ============================================================
CREATE OR REPLACE FUNCTION public.update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER items_updated_at
    BEFORE UPDATE ON public.items
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at();
