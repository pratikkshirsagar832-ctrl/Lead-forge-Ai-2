'use client';

import { useState, useEffect, useCallback } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { useSearch } from '@/hooks/useSearch';
import api from '@/lib/api';
import type { SubscriptionInfo } from '@/lib/types';
import { GlassCard } from '@/components/shared/GlassCard';
import { Badge } from '@/components/shared/Badge';
import { LoadingButton } from '@/components/shared/LoadingButton';
import { SearchProgressCard } from '@/components/dashboard/SearchProgressCard';
import { UpgradeModal } from '@/components/shared/UpgradeModal';
import { API_ROUTES } from '@/lib/constants';
import { useSearchStore } from '@/stores/searchStore';
import { MapPin, Briefcase, SearchIcon, Sparkles, Globe, Star, Phone, ChevronRight, Users, AlertCircle, Linkedin, Clock, LogIn, Loader2, Quote, ExternalLink, Zap, Target, Filter, Cookie, Activity, Hash, Search } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import Link from 'next/link';
import { LEAD_CATEGORIES } from '@/lib/constants';

type SearchSource = 'google_maps' | 'linkedin';

const mapsSchema = z.object({
  niche: z.string().min(2, 'Niche must be at least 2 characters'),
  location: z.string().min(2, 'Location must be at least 2 characters'),
});

const linkedinSchema = z.object({
  keyword: z.string().min(2, 'Keyword must be at least 2 characters'),
});

type LinkedInLeadType = 'all' | 'intern' | 'agency' | 'company' | 'one_client';
type LinkedInTimeFilter = 'latest' | '7_days' | '14_days' | '27_days' | '2_months';

const LINKEDIN_TIME_OPTIONS: { label: string; value: LinkedInTimeFilter }[] = [
  { label: 'Latest', value: 'latest' },
  { label: '7 Days', value: '7_days' },
  { label: '14 Days', value: '14_days' },
  { label: '27 Days', value: '27_days' },
  { label: '2 Months', value: '2_months' },
];

const LEAD_TYPE_OPTIONS: { label: string; value: LinkedInLeadType; desc: string }[] = [
  { label: 'All', value: 'all', desc: 'Any buying intent' },
  { label: 'Intern', value: 'intern', desc: 'Internship / entry-level' },
  { label: 'Agency', value: 'agency', desc: 'Looking for agency' },
  { label: 'Company', value: 'company', desc: 'Full-time hiring' },
  { label: 'One Client', value: 'one_client', desc: 'One-time project' },
];

function LiveResultCard({ lead, index }: { lead: any; index: number }) {
  const isLinkedIn = lead.source === 'linkedin';

  if (isLinkedIn) {
    const scorePercent = lead.intent_score != null ? Math.round(lead.intent_score * 100) : 0;
    return (
      <motion.div
        initial={{ opacity: 0, y: 20, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.4, delay: index * 0.08, ease: 'easeOut' }}
      >
        <Link href={`/dashboard/leads/${lead.id}`} className="block group">
          <div className="glass-card-premium rounded-xl hover:border-accent-cyan/20 transition-all duration-300 hover:-translate-y-1">
            <div className="p-4">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2 min-w-0">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-accent-cyan/20 to-accent-purple/20 flex items-center justify-center shrink-0 ring-1 ring-accent-cyan/20">
                    <Users className="w-4 h-4 text-accent-cyan" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-offwhite truncate">{lead.author_name || 'LinkedIn User'}</p>
                  </div>
                </div>
                {lead.intent_score >= 0.7 && (
                  <span className="flex items-center gap-1 px-2 py-0.5 rounded-md bg-emerald-500/10 border border-emerald-500/20 text-[11px] text-emerald-400 font-semibold shrink-0">
                    <Zap className="w-3 h-3" />
                    {scorePercent}%
                  </span>
                )}
              </div>
              {lead.post_text && (
                <p className="text-xs text-ice/70 leading-relaxed line-clamp-3 mb-3 font-light">
                  <Quote className="w-3 h-3 text-accent-cyan/30 inline-block mr-1" />
                  {lead.post_text}
                </p>
              )}
              <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-ice/40">
                {lead.author_profile && (
                  <a
                    href={lead.author_profile}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={(e) => e.stopPropagation()}
                    className="flex items-center gap-1 text-accent-cyan/60 hover:text-accent-cyan transition-colors"
                  >
                    <ExternalLink className="w-3 h-3" />
                    View Profile
                  </a>
                )}
                {lead.post_url && (
                  <a
                    href={lead.post_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={(e) => e.stopPropagation()}
                    className="flex items-center gap-1 text-accent-cyan/60 hover:text-accent-cyan transition-colors"
                  >
                    <ExternalLink className="w-3 h-3" />
                    View Post
                  </a>
                )}
                {lead.intent_reason && (
                  <span className="truncate italic text-ice/40">{lead.intent_reason}</span>
                )}
              </div>
            </div>
            <div className="px-4 py-2 border-t border-white/5 flex items-center justify-between text-[10px] font-semibold text-accent-cyan/50 group-hover:text-accent-cyan transition-colors">
              <span>View Lead</span>
              <ChevronRight className="w-3 h-3 transition-transform group-hover:translate-x-0.5" />
            </div>
          </div>
        </Link>
      </motion.div>
    );
  }

  const catKey = lead.lead_category || 'warm';
  const catCfg = LEAD_CATEGORIES[catKey as keyof typeof LEAD_CATEGORIES] || { label: catKey, color: '#94a3b8', bg: '#f1f5f9' };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.4, delay: index * 0.08, ease: 'easeOut' }}
    >
      <Link href={`/dashboard/leads/${lead.id}`} className="block group">
        <div className="glass-card-premium rounded-xl hover:border-steel/30 transition-all duration-300 hover:-translate-y-1">
          <div className="p-4">
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-2">
                <Badge
                  style={{ backgroundColor: (catCfg as any).bg, color: catCfg.color }}
                  className="font-bold border-0 text-[10px] px-2 py-0.5"
                >
                  {catCfg.label}
                </Badge>
                {lead.website_health_score != null && (
                  <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                    lead.website_health_score >= 70 ? 'text-emerald-400 bg-emerald-500/10' :
                    lead.website_health_score >= 40 ? 'text-amber-400 bg-amber-500/10' :
                    'text-rose-400 bg-rose-500/10'
                  }`}>
                    {lead.website_health_score}
                  </span>
                )}
              </div>
              <span className="text-[10px] text-ice/30 font-mono">#{index + 1}</span>
            </div>
            <h4 className="text-sm font-bold text-offwhite mb-1.5 truncate group-hover:text-steel transition-colors">
              {lead.business_name || 'Unknown Business'}
            </h4>
            <div className="flex items-center gap-2 text-[11px] text-ice/50 mb-1">
              {lead.rating != null && (
                <span className="flex items-center gap-0.5">
                  <Star className="w-3 h-3 fill-amber-400 text-amber-400" />
                  {lead.rating}
                </span>
              )}
              {lead.category && <span className="text-ice/40">{lead.category}</span>}
            </div>
            <div className="space-y-1 text-[11px] text-ice/60">
              {lead.phone && (
                <div className="flex items-center gap-1.5">
                  <Phone className="w-3 h-3 text-steel/60" />
                  <span>{lead.phone}</span>
                </div>
              )}
              <div className="flex items-center gap-1.5">
                <Globe className="w-3 h-3 text-steel/60 shrink-0" />
                {lead.website_url ? (
                  <span className="truncate">{lead.website_url.replace(/^https?:\/\/(www\.)?/, '')}</span>
                ) : (
                  <span className="text-ice/30 italic">No website</span>
                )}
              </div>
            </div>
          </div>
          <div className="px-4 py-2 border-t border-white/5 flex items-center justify-between text-[10px] font-semibold text-steel/60 group-hover:text-steel transition-colors">
            <span>View Profile</span>
            <ChevronRight className="w-3 h-3 transition-transform group-hover:translate-x-0.5" />
          </div>
        </div>
      </Link>
    </motion.div>
  );
}

export default function SearchPage() {
  const {
    activeSearchId,
    progress,
    results,
    resultsTotal,
    isStarting,
    isCancelling,
    startSearch,
    cancelSearch,
    resumePollingIfActive,
    clearActiveSearch,
  } = useSearch();

  const [source, setSource] = useState<SearchSource>('google_maps');
  const [subscription, setSubscription] = useState<SubscriptionInfo | null>(null);
  const [linkedinKeyword, setLinkedinKeyword] = useState('');
  const [linkedinTimeFilter, setLinkedinTimeFilter] = useState<LinkedInTimeFilter>('latest');
  const [linkedinLeadType, setLinkedinLeadType] = useState<LinkedInLeadType>('all');
  const [linkedinSessionOk, setLinkedinSessionOk] = useState<boolean | null>(null);
  const [linkedinCookieJson, setLinkedinCookieJson] = useState('');
  const [linkedinImporting, setLinkedinImporting] = useState(false);
  const [linkedinImportError, setLinkedinImportError] = useState('');
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  const [isLoadingMore, setIsLoadingMore] = useState(false);

  const mapsForm = useForm({ resolver: zodResolver(mapsSchema) });

  useEffect(() => {
    resumePollingIfActive();
    api.get('/api/auth/me').then(r => setSubscription(r.data?.subscription)).catch(() => {});
  }, [resumePollingIfActive]);

  useEffect(() => {
    if (source === 'linkedin') {
      api.get('/api/linkedin/session/status')
        .then(r => setLinkedinSessionOk(r.data?.logged_in ?? false))
        .catch(() => setLinkedinSessionOk(false));
    }
  }, [source]);

  const remaining = subscription?.remaining_searches ?? 1;
  const searchesPerDay = subscription?.searches_per_day ?? 1;
  const isAtLimit = remaining <= 0;

  const handleImportCookies = useCallback(async () => {
    setLinkedinImporting(true);
    setLinkedinImportError('');
    try {
      const parsed = JSON.parse(linkedinCookieJson);
      const cookies = Array.isArray(parsed) ? parsed : parsed.cookies || [];
      const res = await api.post('/api/linkedin/session/import-cookies', { cookies });
      if (res.data?.success) {
        setLinkedinSessionOk(true);
        setLinkedinCookieJson('');
      } else {
        setLinkedinImportError(res.data?.message || 'Import failed');
      }
    } catch (e: any) {
      setLinkedinImportError('Invalid JSON: ' + e.message);
    } finally {
      setLinkedinImporting(false);
    }
  }, [linkedinCookieJson]);

  const onSubmitMaps = async (data: { niche: string; location: string }) => {
    if (isAtLimit) { setShowUpgradeModal(true); return; }
    try {
      await startSearch(data.niche, data.location);
    } catch (e: any) {
      if (e.response?.status === 429) setShowUpgradeModal(true);
    }
  };

  const onSubmitLinkedin = async () => {
    if (isAtLimit) { setShowUpgradeModal(true); return; }
    if (!linkedinKeyword.trim()) return;
    try {
      await startSearch(linkedinKeyword.trim(), 'linkedin');
    } catch (e: any) {
      if (e.response?.status === 429) setShowUpgradeModal(true);
    }
  };

  const handleLoadMore = useCallback(async () => {
    if (!activeSearchId || isLoadingMore) return;
    setIsLoadingMore(true);
    try {
      const { data } = await api.post(API_ROUTES.searches.loadMore(activeSearchId), {});
      if (data.new_leads > 0) {
        const { data: newResults } = await api.get(`${API_ROUTES.searches.detail(activeSearchId)}/results?page=1&per_page=50`);
        if (newResults.items) {
          useSearchStore.getState().appendResults(newResults.items);
        }
      }
    } catch (e: any) {
      console.error('Load more failed:', e);
    } finally {
      setIsLoadingMore(false);
    }
  }, [activeSearchId, isLoadingMore]);

  const isSearchActive = activeSearchId && progress && !['completed', 'failed', 'cancelled'].includes(progress.status ?? '');

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-offwhite tracking-tight">
            <span className="gradient-text">Finding hot leads</span>
          </h1>
          <p className="text-ice/50 mt-2 text-sm">Find and qualify leads from Google Maps in seconds.</p>
        </div>
      </div>

      {!isSearchActive && !progress && (
        <div className="flex gap-1.5 bg-navy/40 p-1 rounded-2xl border border-ocean/20 backdrop-blur-sm w-fit card-glow">
          <button
            onClick={() => setSource('google_maps')}
            className={`relative flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold transition-all duration-300 ${
              source === 'google_maps'
                ? 'text-offwhite shadow-lg shadow-steel/20'
                : 'text-ice/40 hover:text-ice/70'
            }`}
          >
            {source === 'google_maps' && (
              <motion.div
                layoutId="source-bg"
                className="absolute inset-0 bg-gradient-to-r from-steel/25 to-steel/10 rounded-xl border border-steel/20"
                transition={{ type: 'spring', stiffness: 400, damping: 30 }}
              />
            )}
            <span className="relative z-10 flex items-center gap-2">
              <MapPin className="w-4 h-4" />
              Google Maps
            </span>
          </button>
          <button
            onClick={() => setSource('linkedin')}
            className={`relative flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold transition-all duration-300 ${
              source === 'linkedin'
                ? 'text-offwhite shadow-lg shadow-accent-cyan/10'
                : 'text-ice/40 hover:text-ice/70'
            }`}
          >
            {source === 'linkedin' && (
              <motion.div
                layoutId="source-bg"
                className="absolute inset-0 bg-gradient-to-r from-accent-cyan/20 to-accent-purple/10 rounded-xl border border-accent-cyan/20"
                transition={{ type: 'spring', stiffness: 400, damping: 30 }}
              />
            )}
            <span className="relative z-10 flex items-center gap-2">
              <Linkedin className="w-4 h-4" />
              LinkedIn
            </span>
          </button>
        </div>
      )}

      <AnimatePresence mode="wait">
        {!isSearchActive && !progress ? (
          <motion.div
            key={source}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.3 }}
          >
            {source === 'google_maps' ? (
              <div className="glass-card-premium rounded-2xl p-8 max-w-3xl mx-auto border-ocean/20">
                <form onSubmit={mapsForm.handleSubmit(onSubmitMaps)} className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-medium text-ice/70 mb-2 flex items-center gap-2">
                        <Target className="w-4 h-4 text-steel" />
                        Target Niche
                      </label>
                      <div className="relative group">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                          <Briefcase className="h-5 w-5 text-steel/60 group-focus-within:text-steel transition-colors" />
                        </div>
                        <input
                          {...mapsForm.register('niche')}
                          type="text"
                          placeholder="e.g. Plumbers, Dentists"
                          className="w-full pl-10 pr-4 py-3 rounded-xl border border-ocean/30 bg-navy/60 focus:bg-navy/80 focus:ring-2 focus:ring-steel/40 focus:border-steel/50 transition-all text-offwhite text-lg placeholder-ice/30 outline-none"
                        />
                      </div>
                      {mapsForm.formState.errors.niche && (
                        <p className="text-red-400 text-sm mt-1.5">{mapsForm.formState.errors.niche.message}</p>
                      )}
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-ice/70 mb-2 flex items-center gap-2">
                        <MapPin className="w-4 h-4 text-steel" />
                        Location
                      </label>
                      <div className="relative group">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                          <Globe className="h-5 w-5 text-steel/60 group-focus-within:text-steel transition-colors" />
                        </div>
                        <input
                          {...mapsForm.register('location')}
                          type="text"
                          placeholder="e.g. Dallas TX, London UK"
                          className="w-full pl-10 pr-4 py-3 rounded-xl border border-ocean/30 bg-navy/60 focus:bg-navy/80 focus:ring-2 focus:ring-steel/40 focus:border-steel/50 transition-all text-offwhite text-lg placeholder-ice/30 outline-none"
                        />
                      </div>
                      {mapsForm.formState.errors.location && (
                        <p className="text-red-400 text-sm mt-1.5">{mapsForm.formState.errors.location.message}</p>
                      )}
                    </div>
                  </div>
                  <SearchInfoSection isAtLimit={isAtLimit} remaining={remaining} searchesPerDay={searchesPerDay} isStarting={isStarting} />
                </form>
              </div>
            ) : (
              <div className="max-w-3xl mx-auto">
                {linkedinSessionOk === false ? (
                  <LinkedInCookieImport
                    cookieJson={linkedinCookieJson}
                    onCookieChange={setLinkedinCookieJson}
                    onImport={handleImportCookies}
                    isImporting={linkedinImporting}
                    importError={linkedinImportError}
                    onRetry={() => setLinkedinSessionOk(null)}
                  />
                ) : (
                  <div className="glass-card-premium rounded-2xl p-8 border-accent-cyan/10">
                    <form onSubmit={(e) => { e.preventDefault(); onSubmitLinkedin(); }} className="space-y-6">
                      <div>
                        <label className="block text-sm font-medium text-ice/70 mb-2 flex items-center gap-2">
                          <Hash className="w-4 h-4 text-accent-cyan" />
                          Keyword
                        </label>
                        <div className="relative group">
                          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                            <SearchIcon className="h-5 w-5 text-accent-cyan/60 group-focus-within:text-accent-cyan transition-colors" />
                          </div>
                          <input
                            value={linkedinKeyword}
                            onChange={(e) => setLinkedinKeyword(e.target.value)}
                            type="text"
                            placeholder="e.g. AI automation, website development..."
                            className="w-full pl-10 pr-4 py-3 rounded-xl border border-ocean/30 bg-navy/60 focus:bg-navy/80 focus:ring-2 focus:ring-accent-cyan/40 focus:border-accent-cyan/50 transition-all text-offwhite text-lg placeholder-ice/30 outline-none"
                          />
                        </div>
                      </div>

                      <div>
                        <div className="flex items-center gap-2 mb-3">
                          <Filter className="w-4 h-4 text-ice/50" />
                          <span className="text-xs text-ice/50 font-semibold uppercase tracking-widest">Lead Type</span>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {LEAD_TYPE_OPTIONS.map((opt) => (
                            <motion.button
                              key={opt.value}
                              type="button"
                              onClick={() => setLinkedinLeadType(opt.value)}
                              whileHover={{ scale: 1.02 }}
                              whileTap={{ scale: 0.98 }}
                              className={`relative px-3.5 py-2 rounded-xl text-xs font-semibold transition-all duration-200 ${
                                linkedinLeadType === opt.value
                                  ? 'bg-gradient-to-r from-accent-purple/20 to-accent-purple/10 text-accent-purple border border-accent-purple/30 shadow-lg shadow-accent-purple/10'
                                  : 'bg-navy/40 text-ice/40 border border-ocean/20 hover:border-ocean/40 hover:text-ice/60'
                              }`}
                              title={opt.desc}
                            >
                              {linkedinLeadType === opt.value && (
                                <motion.div
                                  layoutId="lead-type-bg"
                                  className="absolute inset-0 rounded-xl bg-gradient-to-r from-accent-purple/15 to-transparent"
                                  transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                                />
                              )}
                              <span className="relative z-10">{opt.label}</span>
                            </motion.button>
                          ))}
                        </div>
                      </div>

                      <div>
                        <div className="flex items-center gap-2 mb-3">
                          <Activity className="w-4 h-4 text-ice/50" />
                          <span className="text-xs text-ice/50 font-semibold uppercase tracking-widest">Time Filter</span>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {LINKEDIN_TIME_OPTIONS.map((opt) => (
                            <motion.button
                              key={opt.value}
                              type="button"
                              onClick={() => setLinkedinTimeFilter(opt.value)}
                              whileHover={{ scale: 1.02 }}
                              whileTap={{ scale: 0.98 }}
                              className={`relative px-3.5 py-2 rounded-xl text-xs font-semibold transition-all duration-200 ${
                                linkedinTimeFilter === opt.value
                                  ? 'bg-gradient-to-r from-accent-cyan/20 to-accent-cyan/10 text-accent-cyan border border-accent-cyan/30 shadow-lg shadow-accent-cyan/10'
                                  : 'bg-navy/40 text-ice/40 border border-ocean/20 hover:border-ocean/40 hover:text-ice/60'
                              }`}
                            >
                              {linkedinTimeFilter === opt.value && (
                                <motion.div
                                  layoutId="time-bg"
                                  className="absolute inset-0 rounded-xl bg-gradient-to-r from-accent-cyan/15 to-transparent"
                                  transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                                />
                              )}
                              <span className="relative z-10">{opt.label}</span>
                            </motion.button>
                          ))}
                        </div>
                      </div>

                      <div className="bg-gradient-to-r from-accent-cyan/[0.04] to-accent-purple/[0.04] p-4 rounded-xl border border-accent-cyan/10 flex items-start gap-3 neon-glow">
                        <Sparkles className="w-5 h-5 text-accent-cyan shrink-0 mt-0.5" />
                        <p className="text-sm text-ice/60 leading-relaxed">
                          Hyperclients will search LinkedIn for people expressing buying intent, score them with AI, and deliver qualified leads. Results typically in 1-3 minutes.
                        </p>
                      </div>

                      <div className="flex items-center justify-between pt-2">
                        <button
                          type="button"
                          onClick={() => setLinkedinSessionOk(false)}
                          className="text-xs text-ice/30 hover:text-ice/50 transition-colors flex items-center gap-1.5"
                        >
                          <Cookie className="w-3 h-3" />
                          Re-import cookies
                        </button>
                      </div>

                      <div className="flex items-center justify-between pt-4 border-t border-ocean/20">
                        <span className="text-xs text-ice/40">
                          {remaining}/{searchesPerDay} searches remaining today
                        </span>
                        <LoadingButton
                          type="submit"
                          isLoading={isStarting}
                          size="lg"
                          fullWidth={false}
                          variant={isAtLimit ? 'outline' : 'gradient-cyan'}
                          className="text-lg py-4 px-8"
                          disabled={isAtLimit}
                        >
                          <SearchIcon className="w-5 h-5" />
                          Start Search
                        </LoadingButton>
                      </div>
                    </form>
                  </div>
                )}
              </div>
            )}
          </motion.div>
        ) : (
          <motion.div
            key="progress"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.3 }}
          >
            <SearchProgressCard onCancel={cancelSearch} isCancelling={isCancelling} />
          </motion.div>
        )}
      </AnimatePresence>

      {(progress || results.length > 0) && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.2 }}
          key="live-results"
        >
          {results.length > 0 && (
            <>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-steel/20 to-ocean/20 flex items-center justify-center">
                    <Users className="w-4 h-4 text-steel" />
                  </div>
                  <h2 className="text-lg font-bold text-offwhite tracking-tight">Live Results</h2>
                </div>
                <span className="text-sm text-ice/40 font-mono">
                  {results.length}{resultsTotal > results.length ? ' / ' + resultsTotal : ''} found
                </span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {results.map((lead, idx) => (
                  <LiveResultCard key={lead.id} lead={lead} index={idx} />
                ))}
              </div>
              {!isSearchActive && resultsTotal > 0 && (
                <div className="flex justify-center mt-6 gap-4 flex-wrap">
                  <Link href="/dashboard/leads"
                    className="btn-gradient-cyan inline-flex items-center justify-center px-6 py-2.5 rounded-xl text-sm shadow-lg hover:-translate-y-0.5 transition-all"
                  >
                    View All Leads in Dashboard
                  </Link>
                  {results.length >= 10 && (
                    <LoadingButton
                      onClick={handleLoadMore}
                      isLoading={isLoadingMore}
                      variant="glass"
                      size="md"
                    >
                      <Search className="w-4 h-4 mr-1.5" />
                      Load 10 More
                    </LoadingButton>
                  )}
                  <LoadingButton
                    onClick={() => { clearActiveSearch(); }}
                    variant="glass"
                    size="md"
                  >
                    New Search
                  </LoadingButton>
                </div>
              )}
            </>
          )}
        </motion.div>
      )}

      <UpgradeModal isOpen={showUpgradeModal} onClose={() => setShowUpgradeModal(false)} type="limit" />
    </div>
  );
}

function SearchInfoSection({ isAtLimit, remaining, searchesPerDay, isStarting }: { isAtLimit: boolean; remaining: number; searchesPerDay: number; isStarting: boolean }) {
  return (
    <>
      {isAtLimit ? (
        <div className="bg-rose-500/10 p-4 rounded-xl border border-rose-500/30 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
          <div>
            <p className="text-sm text-rose-300 font-semibold">Daily search limit reached</p>
            <p className="text-xs text-rose-400/80 mt-1">You&apos;ve used all {searchesPerDay} searches today. Upgrade your plan or wait until tomorrow.</p>
            <Link href="/dashboard/billing" className="text-xs text-steel hover:underline mt-2 inline-block">Upgrade Plan &rarr;</Link>
          </div>
        </div>
      ) : (
        <div className="bg-steel/10 p-4 rounded-xl border border-steel/20 flex items-start gap-3">
          <Sparkles className="w-5 h-5 text-steel shrink-0 mt-0.5" />
          <p className="text-sm text-ice/70 leading-relaxed">
            Hyperclients will search for targeted results, extract data, and run AI analysis. The process usually takes 2-10 minutes.
          </p>
        </div>
      )}

      <div className="flex items-center justify-between">
        <span className="text-xs text-ice/40">
          {remaining}/{searchesPerDay} searches remaining today
        </span>
        <LoadingButton
          type="submit"
          isLoading={isStarting}
          size="lg"
          fullWidth={false}
          variant={isAtLimit ? 'outline' : 'gradient-cyan'}
          className="text-lg py-4 px-8"
          disabled={isAtLimit}
        >
          <SearchIcon className="w-5 h-5" />
          Start Search
        </LoadingButton>
      </div>
    </>
  );
}

function LinkedInCookieImport({
  cookieJson, onCookieChange, onImport, isImporting, importError, onRetry,
}: {
  cookieJson: string;
  onCookieChange: (v: string) => void;
  onImport: () => void;
  isImporting: boolean;
  importError: string;
  onRetry: () => void;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="glass-card-premium rounded-2xl p-8 md:p-12 max-w-md mx-auto text-center border-accent-cyan/10"
    >
      <div className="w-16 h-16 rounded-full bg-gradient-to-br from-accent-cyan/20 to-accent-purple/20 flex items-center justify-center mx-auto mb-5 ring-1 ring-accent-cyan/20">
        <Linkedin className="w-8 h-8 text-accent-cyan" />
      </div>
      <h2 className="text-xl font-bold text-offwhite mb-2">LinkedIn Session Required</h2>
      <p className="text-sm text-ice/50 mb-4 leading-relaxed">
        Log into LinkedIn on your computer, install the Cookie-Editor extension, export cookies as JSON, then paste here.
      </p>

      <textarea
        rows={6}
        placeholder='[{&quot;name&quot;:&quot;li_at&quot;,&quot;value&quot;:&quot;...&quot;,...}]'
        value={cookieJson}
        onChange={(e) => onCookieChange(e.target.value)}
        disabled={isImporting}
        className="w-full px-4 py-3 rounded-xl text-sm bg-navy/60 border border-ocean/30 text-offwhite placeholder-ice/30 focus:outline-none focus:border-accent-cyan/50 focus:ring-1 focus:ring-accent-cyan/30 mb-4 resize-none font-mono transition-all"
      />

      {importError && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3 mb-4">
          <p className="text-sm text-red-400">{importError}</p>
        </div>
      )}

      <button
        onClick={onImport}
        disabled={isImporting || !cookieJson.trim()}
        className="w-full h-11 rounded-xl font-semibold text-sm flex items-center justify-center gap-2 btn-gradient-cyan disabled:opacity-50 transition-all"
      >
        {isImporting ? (
          <><Loader2 className="w-4 h-4 animate-spin" /> Importing...</>
        ) : (
          <><LogIn className="w-4 h-4" /> Import Cookies</>
        )}
      </button>

      <button
        onClick={onRetry}
        className="text-xs text-ice/30 hover:text-ice/50 mt-4 transition-colors"
      >
        Check session status
      </button>
    </motion.div>
  );
}
