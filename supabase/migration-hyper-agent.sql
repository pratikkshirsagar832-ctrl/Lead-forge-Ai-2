-- Hyper Agent Integration Migration
-- Run this AFTER migration.sql to add Hyper Agent support

-- ═══════════════════════════════════════════════════════════════
-- 1. UPDATE LEADS TABLE — allow hyper_agent source
-- ═══════════════════════════════════════════════════════════════
ALTER TABLE public.leads DROP CONSTRAINT IF EXISTS leads_source_check;
ALTER TABLE public.leads ADD CONSTRAINT leads_source_check
  CHECK (source IN ('google_maps', 'hyper_agent'));

ALTER TABLE public.searches DROP CONSTRAINT IF EXISTS searches_source_check;
ALTER TABLE public.searches ADD CONSTRAINT searches_source_check
  CHECK (source IN ('google_maps', 'hyper_agent'));

-- ═══════════════════════════════════════════════════════════════
-- 2. HYPER CONVERSATIONS
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
-- 3. HYPER MESSAGES
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
-- 4. HYPER CAMPAIGNS
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
-- 5. HYPER VERIFICATION LOGS
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
-- 6. HYPER SETTINGS
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
-- 7. RLS POLICIES
-- ═══════════════════════════════════════════════════════════════
ALTER TABLE public.hyper_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.hyper_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.hyper_campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.hyper_verification_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.hyper_settings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own conversations"
  ON public.hyper_conversations FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own conversations"
  ON public.hyper_conversations FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own conversations"
  ON public.hyper_conversations FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own conversations"
  ON public.hyper_conversations FOR DELETE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can view own messages"
  ON public.hyper_messages FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own messages"
  ON public.hyper_messages FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can view own campaigns"
  ON public.hyper_campaigns FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own campaigns"
  ON public.hyper_campaigns FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own campaigns"
  ON public.hyper_campaigns FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can view own verifications"
  ON public.hyper_verification_logs FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own verifications"
  ON public.hyper_verification_logs FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can view own settings"
  ON public.hyper_settings FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can upsert own settings"
  ON public.hyper_settings FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own settings"
  ON public.hyper_settings FOR UPDATE
  USING (auth.uid() = user_id);
