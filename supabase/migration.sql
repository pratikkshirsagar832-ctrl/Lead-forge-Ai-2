-- ═══════════════════════════════════════════════════════════════
-- HYPERCLIENTS — COMPLETE SCHEMA MIGRATION
-- Run this in Supabase SQL Editor
-- ═══════════════════════════════════════════════════════════════

-- ═══════════════════════════════════════════════════════════════
-- 1. EXTENSION
-- ═══════════════════════════════════════════════════════════════
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ═══════════════════════════════════════════════════════════════
-- 2. PLANS (reference lookup, static data)
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS public.plans (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    leads_per_day INTEGER NOT NULL CHECK (leads_per_day >= 0),
    searches_per_day INTEGER NOT NULL DEFAULT 1 CHECK (searches_per_day >= 0),
    price_monthly INTEGER NOT NULL DEFAULT 0 CHECK (price_monthly >= 0),
    trial_days INTEGER DEFAULT 0 CHECK (trial_days >= 0),
    billing_cycle_days INTEGER DEFAULT 30,
    features JSONB DEFAULT '[]'::jsonb,
    is_active BOOLEAN DEFAULT true,
    sort_order INTEGER DEFAULT 0
);

INSERT INTO public.plans (id, name, description, leads_per_day, searches_per_day, price_monthly, trial_days, billing_cycle_days, features, sort_order) VALUES
    ('free', 'Free',     '3 searches per day, 3 day trial',  30,  3, 0,      3, 30, '["3 searches/day", "30 leads/day", "3-day trial", "Basic filters"]'::jsonb, 0),
    ('solo', 'Solo',     '50 leads/day for freelancers',     50,  5, 99900,  0, 30, '["50 leads/day", "5 searches/day", "Email export", "Website analysis"]'::jsonb, 1),
    ('pro',  'Pro',      '150 leads/day for growing agencies',150,15, 249900, 0, 30, '["150 leads/day", "15 searches/day", "AI pitch generation", "Pipeline management", "Priority support"]'::jsonb, 2),
    ('agency', 'Agency', '500 leads/day for teams',           500, 50, 699900, 0, 30, '["500 leads/day", "50 searches/day", "Everything in Pro", "Team access", "API access", "Dedicated support"]'::jsonb, 3)
ON CONFLICT (id) DO NOTHING;

-- ═══════════════════════════════════════════════════════════════
-- 3. USERS (synced from auth.users for backend operations)
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT DEFAULT '',
    name TEXT DEFAULT '',
    avatar_url TEXT DEFAULT '',
    auth_provider TEXT DEFAULT '',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);

-- ═══════════════════════════════════════════════════════════════
-- 4. USER SUBSCRIPTIONS
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS public.user_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    plan_id TEXT NOT NULL REFERENCES public.plans(id) DEFAULT 'free',
    status TEXT NOT NULL DEFAULT 'trial' CHECK (status IN ('trial', 'active', 'past_due', 'cancelled', 'expired')),
    current_period_start TIMESTAMPTZ DEFAULT NOW(),
    current_period_end TIMESTAMPTZ,
    trial_end TIMESTAMPTZ,
    razorpay_subscription_id TEXT,
    razorpay_order_id TEXT,
    razorpay_payment_id TEXT,
    cancelled_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_subscriptions_user_id ON public.user_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_plan_id ON public.user_subscriptions(plan_id);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_status ON public.user_subscriptions(status);

-- ═══════════════════════════════════════════════════════════════
-- 5. DAILY USAGE TRACKING
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS public.daily_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    leads_generated INTEGER DEFAULT 0 CHECK (leads_generated >= 0),
    searches_run INTEGER DEFAULT 0 CHECK (searches_run >= 0),
    ai_calls INTEGER DEFAULT 0 CHECK (ai_calls >= 0),
    UNIQUE(user_id, date)
);

CREATE INDEX IF NOT EXISTS idx_daily_usage_user_date ON public.daily_usage(user_id, date);

-- ═══════════════════════════════════════════════════════════════
-- 6. SEARCHES
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS public.searches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    niche TEXT NOT NULL,
    location TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'google_maps' CHECK (source IN ('google_maps', 'hyper_agent')),
    status TEXT NOT NULL DEFAULT 'queued'
        CHECK (status IN ('queued', 'scraping', 'analyzing', 'completed', 'failed', 'cancelled')),
    progress_percent INTEGER DEFAULT 0 CHECK (progress_percent >= 0 AND progress_percent <= 100),
    message TEXT DEFAULT 'Search queued',
    total_results INTEGER DEFAULT 0 CHECK (total_results >= 0),
    hot_leads INTEGER DEFAULT 0 CHECK (hot_leads >= 0),
    warm_leads INTEGER DEFAULT 0 CHECK (warm_leads >= 0),
    skipped INTEGER DEFAULT 0 CHECK (skipped >= 0),
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_searches_user_id ON public.searches(user_id);
CREATE INDEX IF NOT EXISTS idx_searches_status ON public.searches(status);
CREATE INDEX IF NOT EXISTS idx_searches_created_at ON public.searches(created_at DESC);

-- ═══════════════════════════════════════════════════════════════
-- 7. LEADS
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS public.leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    search_id UUID NOT NULL REFERENCES public.searches(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    source TEXT NOT NULL DEFAULT 'google_maps' CHECK (source IN ('google_maps', 'hyper_agent')),
    google_key TEXT DEFAULT '',
    business_name TEXT NOT NULL,
    category TEXT DEFAULT '',
    full_address TEXT DEFAULT '',
    phone TEXT DEFAULT '',
    email_found TEXT DEFAULT '',
    website_url TEXT DEFAULT '',
    rating DOUBLE PRECISION CHECK (rating IS NULL OR (rating >= 0 AND rating <= 5)),
    total_reviews INTEGER DEFAULT 0 CHECK (total_reviews >= 0),
    google_maps_link TEXT DEFAULT '',
    photos JSONB DEFAULT '[]'::jsonb,
    business_hours JSONB DEFAULT '{}'::jsonb,
    description TEXT DEFAULT '',
    lead_category TEXT DEFAULT 'warm' CHECK (lead_category IN ('hot', 'warm')),
    website_health_score INTEGER CHECK (website_health_score IS NULL OR (website_health_score >= 0 AND website_health_score <= 100)),
    ai_pitch TEXT,
    ai_confidence_score DOUBLE PRECISION CHECK (ai_confidence_score IS NULL OR (ai_confidence_score >= 0 AND ai_confidence_score <= 1)),
    estimated_deal_value DOUBLE PRECISION CHECK (estimated_deal_value IS NULL OR estimated_deal_value >= 0),
    user_status TEXT DEFAULT 'new' CHECK (user_status IN ('new', 'contacted', 'replied', 'converted', 'lost')),
    user_notes TEXT DEFAULT '',
    is_favorite BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_leads_search_id ON public.leads(search_id);
CREATE INDEX IF NOT EXISTS idx_leads_user_id ON public.leads(user_id);
CREATE INDEX IF NOT EXISTS idx_leads_lead_category ON public.leads(lead_category);
CREATE INDEX IF NOT EXISTS idx_leads_user_status ON public.leads(user_status);
CREATE INDEX IF NOT EXISTS idx_leads_is_favorite ON public.leads(is_favorite);
CREATE INDEX IF NOT EXISTS idx_leads_business_name ON public.leads USING gin(business_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_leads_created_at ON public.leads(created_at DESC);

-- ═══════════════════════════════════════════════════════════════
-- 8. WEBSITE ANALYSES
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS public.website_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID NOT NULL REFERENCES public.leads(id) ON DELETE CASCADE,
    website_url TEXT NOT NULL,
    overall_score INTEGER DEFAULT 0 CHECK (overall_score >= 0 AND overall_score <= 100),
    issues JSONB DEFAULT '[]'::jsonb,
    emails_found JSONB DEFAULT '[]'::jsonb,
    phones_found JSONB DEFAULT '[]'::jsonb,
    raw_analysis JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_website_analyses_lead_id ON public.website_analyses(lead_id);

-- ═══════════════════════════════════════════════════════════════
-- 9. HYPER CONVERSATIONS (Hyper Agent)
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS public.hyper_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT DEFAULT '',
    intent TEXT DEFAULT '',
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'archived', 'completed')),
    lead_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_hyper_conversations_user_id ON public.hyper_conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_hyper_conversations_status ON public.hyper_conversations(status);
CREATE INDEX IF NOT EXISTS idx_hyper_conversations_created_at ON public.hyper_conversations(created_at DESC);

-- ═══════════════════════════════════════════════════════════════
-- 10. HYPER MESSAGES
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS public.hyper_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES public.hyper_conversations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    intent JSONB DEFAULT '{}'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_hyper_messages_conversation_id ON public.hyper_messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_hyper_messages_user_id ON public.hyper_messages(user_id);
CREATE INDEX IF NOT EXISTS idx_hyper_messages_created_at ON public.hyper_messages(created_at);

-- ═══════════════════════════════════════════════════════════════
-- 11. HYPER CAMPAIGNS
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS public.hyper_campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'paused', 'completed', 'archived')),
    type TEXT DEFAULT 'email' CHECK (type IN ('email', 'sequence', 'multi-channel')),
    target_count INTEGER DEFAULT 0,
    sent_count INTEGER DEFAULT 0,
    open_count INTEGER DEFAULT 0,
    reply_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_hyper_campaigns_user_id ON public.hyper_campaigns(user_id);
CREATE INDEX IF NOT EXISTS idx_hyper_campaigns_status ON public.hyper_campaigns(status);
CREATE INDEX IF NOT EXISTS idx_hyper_campaigns_created_at ON public.hyper_campaigns(created_at DESC);

-- ═══════════════════════════════════════════════════════════════
-- 12. HYPER VERIFICATION LOGS
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS public.hyper_verification_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('valid', 'invalid', 'risky', 'unknown')),
    confidence DOUBLE PRECISION CHECK (confidence >= 0 AND confidence <= 1),
    checks JSONB DEFAULT '{}'::jsonb,
    duration_ms INTEGER,
    source TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_hyper_verification_logs_user_id ON public.hyper_verification_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_hyper_verification_logs_status ON public.hyper_verification_logs(status);
CREATE INDEX IF NOT EXISTS idx_hyper_verification_logs_created_at ON public.hyper_verification_logs(created_at DESC);

-- ═══════════════════════════════════════════════════════════════
-- 13. HYPER SETTINGS
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS public.hyper_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    settings JSONB DEFAULT '{}'::jsonb NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id)
);

CREATE INDEX IF NOT EXISTS idx_hyper_settings_user_id ON public.hyper_settings(user_id);

-- ═══════════════════════════════════════════════════════════════
-- 14. TRIGGERS
-- ═══════════════════════════════════════════════════════════════

-- Auto-create subscription and user record on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.user_subscriptions (user_id, plan_id, status, trial_end, current_period_end)
    VALUES (
        NEW.id, 'free', 'trial',
        NOW() + INTERVAL '3 days',
        NOW() + INTERVAL '3 days'
    );

    INSERT INTO public.users (id, email)
    VALUES (NEW.id, COALESCE(NEW.email, ''))
    ON CONFLICT (id) DO NOTHING;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Auto-update timestamps
CREATE OR REPLACE FUNCTION public.update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_users_timestamp ON public.users;
CREATE TRIGGER update_users_timestamp
    BEFORE UPDATE ON public.users
    FOR EACH ROW EXECUTE FUNCTION public.update_timestamp();

DROP TRIGGER IF EXISTS on_user_subscriptions_update ON public.user_subscriptions;
CREATE TRIGGER on_user_subscriptions_update
    BEFORE UPDATE ON public.user_subscriptions
    FOR EACH ROW EXECUTE FUNCTION public.update_timestamp();

DROP TRIGGER IF EXISTS on_hyper_conversations_update ON public.hyper_conversations;
CREATE TRIGGER on_hyper_conversations_update
    BEFORE UPDATE ON public.hyper_conversations
    FOR EACH ROW EXECUTE FUNCTION public.update_timestamp();

DROP TRIGGER IF EXISTS on_hyper_campaigns_update ON public.hyper_campaigns;
CREATE TRIGGER on_hyper_campaigns_update
    BEFORE UPDATE ON public.hyper_campaigns
    FOR EACH ROW EXECUTE FUNCTION public.update_timestamp();

DROP TRIGGER IF EXISTS on_hyper_settings_update ON public.hyper_settings;
CREATE TRIGGER on_hyper_settings_update
    BEFORE UPDATE ON public.hyper_settings
    FOR EACH ROW EXECUTE FUNCTION public.update_timestamp();

-- Increment daily_usage.leads_generated on lead insert
CREATE OR REPLACE FUNCTION public.handle_lead_insert()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.daily_usage (user_id, date, leads_generated, searches_run)
    VALUES (NEW.user_id, CURRENT_DATE, 1, 0)
    ON CONFLICT (user_id, date)
    DO UPDATE SET leads_generated = daily_usage.leads_generated + 1;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_lead_insert ON public.leads;
CREATE TRIGGER on_lead_insert
    AFTER INSERT ON public.leads
    FOR EACH ROW EXECUTE FUNCTION public.handle_lead_insert();

-- ═══════════════════════════════════════════════════════════════
-- 15. SYNC: ensure all existing users have subscriptions
-- ═══════════════════════════════════════════════════════════════
INSERT INTO public.user_subscriptions (user_id, plan_id, status, trial_end, current_period_end)
SELECT id, 'free', 'trial', NOW() + INTERVAL '3 days', NOW() + INTERVAL '3 days'
FROM auth.users
WHERE id NOT IN (SELECT user_id FROM public.user_subscriptions)
ON CONFLICT DO NOTHING;

INSERT INTO public.users (id, email)
SELECT id, COALESCE(email, '') FROM auth.users
WHERE id NOT IN (SELECT id FROM public.users)
ON CONFLICT DO NOTHING;

-- ═══════════════════════════════════════════════════════════════
-- 16. FUNCTIONS
-- ═══════════════════════════════════════════════════════════════

-- Get remaining searches today
CREATE OR REPLACE FUNCTION public.get_remaining_searches(p_user_id UUID)
RETURNS INTEGER
LANGUAGE plpgsql STABLE
AS $$
DECLARE
    plan_max INTEGER := 0;
    used_today INTEGER := 0;
BEGIN
    SELECT COALESCE(pl.searches_per_day, 1) INTO plan_max
    FROM user_subscriptions us
    JOIN plans pl ON us.plan_id = pl.id
    WHERE us.user_id = p_user_id AND us.status IN ('active', 'trial');

    SELECT COALESCE(du.searches_run, 0) INTO used_today
    FROM daily_usage du
    WHERE du.user_id = p_user_id AND du.date = CURRENT_DATE;

    RETURN GREATEST(0, COALESCE(plan_max, 1) - COALESCE(used_today, 0));
END;
$$;

-- Get remaining leads today
CREATE OR REPLACE FUNCTION public.get_remaining_leads(p_user_id UUID)
RETURNS INTEGER
LANGUAGE plpgsql STABLE
AS $$
DECLARE
    plan_max INTEGER := 0;
    used_today INTEGER := 0;
BEGIN
    SELECT COALESCE(pl.leads_per_day, 10) INTO plan_max
    FROM user_subscriptions us
    JOIN plans pl ON us.plan_id = pl.id
    WHERE us.user_id = p_user_id AND us.status IN ('active', 'trial');

    SELECT COALESCE(du.leads_generated, 0) INTO used_today
    FROM daily_usage du
    WHERE du.user_id = p_user_id AND du.date = CURRENT_DATE;

    RETURN GREATEST(0, COALESCE(plan_max, 10) - COALESCE(used_today, 0));
END;
$$;

-- Get subscription info (JSON)
CREATE OR REPLACE FUNCTION public.get_user_subscription(p_user_id UUID)
RETURNS JSON
LANGUAGE plpgsql STABLE
AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'plan_id', us.plan_id,
        'plan_name', pl.name,
        'leads_per_day', pl.leads_per_day,
        'searches_per_day', pl.searches_per_day,
        'billing_cycle_days', pl.billing_cycle_days,
        'features', pl.features,
        'status', us.status,
        'trial_end', us.trial_end,
        'current_period_end', us.current_period_end,
        'remaining_searches', get_remaining_searches(p_user_id),
        'remaining_leads', get_remaining_leads(p_user_id),
        'is_trial_expired',
            CASE WHEN us.trial_end < NOW() AND us.plan_id = 'free' THEN true ELSE false END
    ) INTO result
    FROM user_subscriptions us
    JOIN plans pl ON us.plan_id = pl.id
    WHERE us.user_id = p_user_id
    ORDER BY us.created_at DESC
    LIMIT 1;

    RETURN result;
END;
$$;

-- Increment daily usage
CREATE OR REPLACE FUNCTION public.increment_daily_usage(
    p_user_id UUID,
    p_leads INTEGER DEFAULT 0,
    p_searches INTEGER DEFAULT 0,
    p_ai_calls INTEGER DEFAULT 0
) RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO daily_usage (user_id, date, leads_generated, searches_run, ai_calls)
    VALUES (p_user_id, CURRENT_DATE, p_leads, p_searches, p_ai_calls)
    ON CONFLICT (user_id, date)
    DO UPDATE SET
        leads_generated = daily_usage.leads_generated + p_leads,
        searches_run = daily_usage.searches_run + p_searches,
        ai_calls = daily_usage.ai_calls + p_ai_calls;
END;
$$;

-- Dashboard stats
CREATE OR REPLACE FUNCTION public.get_dashboard_stats(p_user_id UUID)
RETURNS JSON
LANGUAGE plpgsql STABLE
AS $$
DECLARE
    total_searches INTEGER;
    total_leads INTEGER;
    hot_leads INTEGER;
    warm_leads INTEGER;
    sub_info JSON;
BEGIN
    SELECT COUNT(*) INTO total_searches FROM searches WHERE user_id = p_user_id;
    SELECT COUNT(*) INTO total_leads FROM leads WHERE user_id = p_user_id;
    SELECT COUNT(*) INTO hot_leads FROM leads WHERE user_id = p_user_id AND lead_category = 'hot';
    SELECT COUNT(*) INTO warm_leads FROM leads WHERE user_id = p_user_id AND lead_category = 'warm';

    sub_info := get_user_subscription(p_user_id);

    RETURN json_build_object(
        'total_searches', total_searches,
        'total_leads', total_leads,
        'hot_leads', hot_leads,
        'warm_leads', warm_leads,
        'subscription', sub_info
    );
END;
$$;

-- Cleanup old daily_usage rows (keep last 90 days)
CREATE OR REPLACE FUNCTION public.cleanup_daily_usage()
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    deleted INTEGER;
BEGIN
    DELETE FROM daily_usage WHERE date < CURRENT_DATE - INTERVAL '90 days';
    GET DIAGNOSTICS deleted = ROW_COUNT;
    RETURN deleted;
END;
$$;

-- ═══════════════════════════════════════════════════════════════
-- 17. ROW LEVEL SECURITY
-- ═══════════════════════════════════════════════════════════════

-- Allow public read for plans (used by unauthenticated billing page)
ALTER TABLE public.plans ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS plans_read_all ON public.plans;
CREATE POLICY plans_read_all ON public.plans
    FOR SELECT USING (true);

ALTER TABLE public.user_subscriptions ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS user_subscriptions_isolation ON public.user_subscriptions;
CREATE POLICY user_subscriptions_isolation ON public.user_subscriptions
    FOR ALL USING (user_id = auth.uid());

ALTER TABLE public.daily_usage ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS daily_usage_isolation ON public.daily_usage;
CREATE POLICY daily_usage_isolation ON public.daily_usage
    FOR ALL USING (user_id = auth.uid());

ALTER TABLE public.searches ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS searches_isolation ON public.searches;
CREATE POLICY searches_isolation ON public.searches
    FOR ALL USING (user_id = auth.uid());

ALTER TABLE public.leads ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS leads_isolation ON public.leads;
CREATE POLICY leads_isolation ON public.leads
    FOR ALL USING (user_id = auth.uid());

ALTER TABLE public.website_analyses ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS website_analyses_isolation ON public.website_analyses;
CREATE POLICY website_analyses_isolation ON public.website_analyses
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.leads
            WHERE leads.id = website_analyses.lead_id
            AND leads.user_id = auth.uid()
        )
    );

ALTER TABLE public.hyper_conversations ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS hyper_conversations_isolation ON public.hyper_conversations;
CREATE POLICY hyper_conversations_isolation ON public.hyper_conversations
    FOR ALL USING (auth.uid() = user_id);

ALTER TABLE public.hyper_messages ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS hyper_messages_isolation ON public.hyper_messages;
CREATE POLICY hyper_messages_isolation ON public.hyper_messages
    FOR ALL USING (auth.uid() = user_id);

ALTER TABLE public.hyper_campaigns ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS hyper_campaigns_isolation ON public.hyper_campaigns;
CREATE POLICY hyper_campaigns_isolation ON public.hyper_campaigns
    FOR ALL USING (auth.uid() = user_id);

ALTER TABLE public.hyper_verification_logs ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS hyper_verification_logs_isolation ON public.hyper_verification_logs;
CREATE POLICY hyper_verification_logs_isolation ON public.hyper_verification_logs
    FOR ALL USING (auth.uid() = user_id);

ALTER TABLE public.hyper_settings ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS hyper_settings_isolation ON public.hyper_settings;
CREATE POLICY hyper_settings_isolation ON public.hyper_settings
    FOR ALL USING (auth.uid() = user_id);

ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS users_isolation ON public.users;
CREATE POLICY users_isolation ON public.users
    FOR ALL USING (id = auth.uid());
