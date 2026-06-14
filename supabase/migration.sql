-- Hyperclients Auth + Payments Migration
-- Run this in Supabase SQL Editor (https://supabase.com/dashboard/project/wtradahkkpbkbhmkkpal/sql/new)

-- 1. Plans configuration
CREATE TABLE IF NOT EXISTS public.plans (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    leads_per_day INTEGER NOT NULL,
    searches_per_day INTEGER NOT NULL DEFAULT 1,
    price_monthly INTEGER NOT NULL DEFAULT 0,
    trial_days INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    sort_order INTEGER DEFAULT 0
);

INSERT INTO public.plans (id, name, description, leads_per_day, searches_per_day, price_monthly, trial_days, sort_order) VALUES
    ('free', 'Free', '1 search per day, 3 day trial', 10, 1, 0, 3, 0),
    ('solo', 'Solo', '50 leads/day for freelancers', 50, 5, 99900, 0, 1),
    ('pro', 'Pro', '150 leads/day for growing agencies', 150, 15, 249900, 0, 2),
    ('agency', 'Agency', '500 leads/day for teams', 500, 50, 699900, 0, 3)
ON CONFLICT (id) DO NOTHING;

-- 2. User subscriptions
CREATE TABLE IF NOT EXISTS public.user_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    plan_id TEXT NOT NULL REFERENCES public.plans(id) DEFAULT 'free',
    status TEXT NOT NULL DEFAULT 'trial',
    current_period_start TIMESTAMPTZ DEFAULT NOW(),
    current_period_end TIMESTAMPTZ,
    trial_end TIMESTAMPTZ,
    razorpay_subscription_id TEXT,
    razorpay_order_id TEXT,
    cancelled_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_subscriptions_user_id ON public.user_subscriptions(user_id);

-- 3. Daily usage tracking
CREATE TABLE IF NOT EXISTS public.daily_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    leads_generated INTEGER DEFAULT 0,
    searches_run INTEGER DEFAULT 0,
    ai_calls INTEGER DEFAULT 0,
    UNIQUE(user_id, date)
);

CREATE INDEX IF NOT EXISTS idx_daily_usage_user_date ON public.daily_usage(user_id, date);

-- 4. Auto-create subscription on user signup
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

-- 5. Sync existing users who don't have subscriptions
INSERT INTO public.user_subscriptions (user_id, plan_id, status, trial_end, current_period_end)
SELECT id, 'free', 'trial', NOW() + INTERVAL '3 days', NOW() + INTERVAL '3 days'
FROM auth.users
WHERE id NOT IN (SELECT user_id FROM public.user_subscriptions)
ON CONFLICT DO NOTHING;

-- 6. Function: get remaining searches today
CREATE OR REPLACE FUNCTION public.get_remaining_searches(p_user_id UUID)
RETURNS INTEGER AS $$
DECLARE
    plan_max INTEGER;
    used_today INTEGER;
BEGIN
    SELECT COALESCE(pl.searches_per_day, 1) INTO plan_max
    FROM user_subscriptions us
    JOIN plans pl ON us.plan_id = pl.id
    WHERE us.user_id = p_user_id AND us.status IN ('active', 'trial');

    SELECT COALESCE(du.searches_run, 0) INTO used_today
    FROM daily_usage du
    WHERE du.user_id = p_user_id AND du.date = CURRENT_DATE;

    RETURN GREATEST(0, plan_max - used_today);
END;
$$ LANGUAGE plpgsql;

-- 7. Function: get subscription info
CREATE OR REPLACE FUNCTION public.get_user_subscription(p_user_id UUID)
RETURNS JSON AS $$
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
        'is_trial_expired', CASE WHEN us.trial_end < NOW() AND us.plan_id = 'free' THEN true ELSE false END
    ) INTO result
    FROM user_subscriptions us
    JOIN plans pl ON us.plan_id = pl.id
    WHERE us.user_id = p_user_id;

    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- 8. Function: increment daily usage
CREATE OR REPLACE FUNCTION public.increment_daily_usage(
    p_user_id UUID,
    p_leads INTEGER DEFAULT 0,
    p_searches INTEGER DEFAULT 0,
    p_ai_calls INTEGER DEFAULT 0
) RETURNS VOID AS $$
BEGIN
    INSERT INTO daily_usage (user_id, date, leads_generated, searches_run, ai_calls)
    VALUES (p_user_id, CURRENT_DATE, p_leads, p_searches, p_ai_calls)
    ON CONFLICT (user_id, date)
    DO UPDATE SET
        leads_generated = daily_usage.leads_generated + p_leads,
        searches_run = daily_usage.searches_run + p_searches,
        ai_calls = daily_usage.ai_calls + p_ai_calls;
END;
$$ LANGUAGE plpgsql;

-- 9. Dashboard stats function (update existing or create)
CREATE OR REPLACE FUNCTION public.get_dashboard_stats(p_user_id UUID)
RETURNS JSON AS $$
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
$$ LANGUAGE plpgsql;

-- 10. Enable RLS on tables (defense in depth)
ALTER TABLE public.user_subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.daily_usage ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS user_subscriptions_isolation ON public.user_subscriptions;
CREATE POLICY user_subscriptions_isolation ON public.user_subscriptions
    FOR ALL USING (user_id = auth.uid());

DROP POLICY IF EXISTS daily_usage_isolation ON public.daily_usage;
CREATE POLICY daily_usage_isolation ON public.daily_usage
    FOR ALL USING (user_id = auth.uid());
