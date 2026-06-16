-- Hyperclients — Complete Schema Migration
-- Run this in Supabase SQL Editor (https://supabase.com/dashboard/project/wtradahkkpbkbhmkkpal/sql/new)

-- ═══════════════════════════════════════════════════════════════
-- 1. PLANS (reference lookup, static data)
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS public.plans (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    leads_per_day INTEGER NOT NULL CHECK (leads_per_day >= 0),
    searches_per_day INTEGER NOT NULL DEFAULT 1 CHECK (searches_per_day >= 0),
    price_monthly INTEGER NOT NULL DEFAULT 0 CHECK (price_monthly >= 0),
    trial_days INTEGER DEFAULT 0 CHECK (trial_days >= 0),
    is_active BOOLEAN DEFAULT true,
    sort_order INTEGER DEFAULT 0
);

INSERT INTO public.plans (id, name, description, leads_per_day, searches_per_day, price_monthly, trial_days, sort_order) VALUES
    ('free', 'Free', '3 searches per day, 3 day trial', 30, 3, 0, 3, 0),
    ('solo', 'Solo', '50 leads/day for freelancers', 50, 5, 99900, 0, 1),
    ('pro', 'Pro', '150 leads/day for growing agencies', 150, 15, 249900, 0, 2),
    ('agency', 'Agency', '500 leads/day for teams', 500, 50, 699900, 0, 3)
ON CONFLICT (id) DO NOTHING;

-- ═══════════════════════════════════════════════════════════════
-- 2. USER SUBSCRIPTIONS
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

-- Add payment_id column if table already existed without it
ALTER TABLE public.user_subscriptions ADD COLUMN IF NOT EXISTS razorpay_payment_id TEXT;

-- ═══════════════════════════════════════════════════════════════
-- 3. DAILY USAGE TRACKING
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
-- 4. SEARCHES (pipeline runs)
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS public.searches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    niche TEXT NOT NULL,
    location TEXT NOT NULL,
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
-- 5. LEADS
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS public.leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    search_id UUID NOT NULL REFERENCES public.searches(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
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
-- 6. WEBSITE ANALYSES
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
-- 7. TRIGGER: auto-create subscription on user signup
-- ═══════════════════════════════════════════════════════════════
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.user_subscriptions (user_id, plan_id, status, trial_end, current_period_end)
    VALUES (
        NEW.id,
        'free',
        'trial',
        NOW() + INTERVAL '3 days',
        NOW() + INTERVAL '3 days'
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ═══════════════════════════════════════════════════════════════
-- 8. TRIGGER: auto-update subscription updated_at
-- ═══════════════════════════════════════════════════════════════
CREATE OR REPLACE FUNCTION public.update_subscription_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS on_user_subscriptions_update ON public.user_subscriptions;
CREATE TRIGGER on_user_subscriptions_update
    BEFORE UPDATE ON public.user_subscriptions
    FOR EACH ROW EXECUTE FUNCTION public.update_subscription_timestamp();

-- ═══════════════════════════════════════════════════════════════
-- 9. TRIGGER: increment daily_usage.leads_generated on lead insert
-- ═══════════════════════════════════════════════════════════════
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
-- 10. SYNC: ensure all existing users have subscriptions
-- ═══════════════════════════════════════════════════════════════
INSERT INTO public.user_subscriptions (user_id, plan_id, status, trial_end, current_period_end)
SELECT id, 'free', 'trial', NOW() + INTERVAL '3 days', NOW() + INTERVAL '3 days'
FROM auth.users
WHERE id NOT IN (SELECT user_id FROM public.user_subscriptions)
ON CONFLICT DO NOTHING;

-- ═══════════════════════════════════════════════════════════════
-- 11. FUNCTION: get remaining searches today
-- ═══════════════════════════════════════════════════════════════
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

-- ═══════════════════════════════════════════════════════════════
-- 12. FUNCTION: get remaining leads today
-- ═══════════════════════════════════════════════════════════════
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

-- ═══════════════════════════════════════════════════════════════
-- 13. FUNCTION: get subscription info (JSON)
-- ═══════════════════════════════════════════════════════════════
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

-- ═══════════════════════════════════════════════════════════════
-- 14. FUNCTION: increment daily usage
-- ═══════════════════════════════════════════════════════════════
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

-- ═══════════════════════════════════════════════════════════════
-- 15. FUNCTION: dashboard stats
-- ═══════════════════════════════════════════════════════════════
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

-- ═══════════════════════════════════════════════════════════════
-- 16. ROW LEVEL SECURITY
-- ═══════════════════════════════════════════════════════════════

-- Enable RLS on all tables
ALTER TABLE public.user_subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.daily_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.searches ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.website_analyses ENABLE ROW LEVEL SECURITY;

-- user_subscriptions: each user sees their own
DROP POLICY IF EXISTS user_subscriptions_isolation ON public.user_subscriptions;
CREATE POLICY user_subscriptions_isolation ON public.user_subscriptions
    FOR ALL USING (user_id = auth.uid());

-- daily_usage: each user sees their own
DROP POLICY IF EXISTS daily_usage_isolation ON public.daily_usage;
CREATE POLICY daily_usage_isolation ON public.daily_usage
    FOR ALL USING (user_id = auth.uid());

-- searches: each user sees their own
DROP POLICY IF EXISTS searches_isolation ON public.searches;
CREATE POLICY searches_isolation ON public.searches
    FOR ALL USING (user_id = auth.uid());

-- leads: each user sees their own
DROP POLICY IF EXISTS leads_isolation ON public.leads;
CREATE POLICY leads_isolation ON public.leads
    FOR ALL USING (user_id = auth.uid());

-- website_analyses: via joined lead ownership
DROP POLICY IF EXISTS website_analyses_isolation ON public.website_analyses;
CREATE POLICY website_analyses_isolation ON public.website_analyses
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.leads
            WHERE leads.id = website_analyses.lead_id
            AND leads.user_id = auth.uid()
        )
    );

-- ═══════════════════════════════════════════════════════════════
-- 17. ENABLE pg_trgm for ILIKE search on leads.business_name
-- ═══════════════════════════════════════════════════════════════
CREATE EXTENSION IF NOT EXISTS pg_trgm;
