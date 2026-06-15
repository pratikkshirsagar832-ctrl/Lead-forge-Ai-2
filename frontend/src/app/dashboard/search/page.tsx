'use client';

import { useState, useEffect } from 'react';
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
import { MapPin, Briefcase, SearchIcon, Sparkles, Globe, Star, Phone, ChevronRight, Users, AlertCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import Link from 'next/link';
import { LEAD_CATEGORIES } from '@/lib/constants';

const searchSchema = z.object({
  niche: z.string().min(2, 'Niche must be at least 2 characters'),
  location: z.string().min(2, 'Location must be at least 2 characters'),
});

type SearchSchema = z.infer<typeof searchSchema>;

function LiveResultCard({ lead, index }: { lead: any; index: number }) {
  const catKey = lead.lead_category || 'warm';
  const catCfg = LEAD_CATEGORIES[catKey as keyof typeof LEAD_CATEGORIES] || { label: catKey, color: '#94a3b8', bg: '#f1f5f9' };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.4, delay: index * 0.08, ease: 'easeOut' }}
    >
      <Link href={`/dashboard/leads/${lead.id}`} className="block group">
        <div className="relative bg-gradient-to-br from-ocean/20 to-navy/80 rounded-xl border border-ocean/30 hover:border-steel/40 transition-all duration-300 overflow-hidden hover:shadow-lg hover:shadow-steel/10 hover:-translate-y-0.5">
          <div className="absolute inset-0 bg-gradient-to-br from-steel/[0.02] to-transparent pointer-events-none" />
          <div className="p-4 relative z-10">
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
              <span className="text-[10px] text-ice/40 font-medium">{index + 1}</span>
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
              {lead.category && <span>{lead.category}</span>}
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
          <div className="px-4 py-2 border-t border-ocean/20 flex items-center justify-between text-[10px] font-semibold text-steel group-hover:text-ice transition-colors">
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
    clearActiveSearch
  } = useSearch();

  const { register, handleSubmit, formState: { errors } } = useForm<SearchSchema>({
    resolver: zodResolver(searchSchema),
  });

  const [subscription, setSubscription] = useState<SubscriptionInfo | null>(null);

  useEffect(() => {
    resumePollingIfActive();
    api.get('/api/auth/me').then(r => setSubscription(r.data?.subscription)).catch(() => {});
  }, [resumePollingIfActive]);

  const remaining = subscription?.remaining_searches ?? 1;
  const searchesPerDay = subscription?.searches_per_day ?? 1;
  const isAtLimit = remaining <= 0;

  const onSubmit = async (data: SearchSchema) => {
    if (isAtLimit) return;
    await startSearch(data.niche, data.location);
  };

  const isSearchActive = activeSearchId && progress && !['completed', 'failed', 'cancelled'].includes(progress.status);

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div>
        <h1 className="text-3xl font-bold text-offwhite tracking-tight">New Search</h1>
        <p className="text-ice/60 mt-2">Find and qualify leads instantly from Google Maps.</p>
      </div>

      <AnimatePresence mode="wait">
        {!isSearchActive && !progress ? (
          <motion.div
            key="form"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.3 }}
          >
            <GlassCard className="p-8 max-w-3xl mx-auto border-ocean/40 bg-gradient-to-br from-ocean/30 to-navy">
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-ice/80 mb-2">
                      Target Niche
                    </label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <Briefcase className="h-5 w-5 text-steel" />
                      </div>
                      <input
                        {...register('niche')}
                        type="text"
                        placeholder="e.g. Plumbers, Dentists"
                        className="w-full pl-10 pr-4 py-3 rounded-xl border border-ocean/50 bg-navy/80 focus:bg-navy focus:ring-2 focus:ring-steel/50 focus:border-steel transition-all text-offwhite text-lg placeholder-ice/40"
                      />
                    </div>
                    {errors.niche && <p className="text-red-400 text-sm mt-1.5">{errors.niche.message}</p>}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-ice/80 mb-2">
                      Location
                    </label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <MapPin className="h-5 w-5 text-steel" />
                      </div>
                      <input
                        {...register('location')}
                        type="text"
                        placeholder="e.g. Dallas TX, London UK"
                        className="w-full pl-10 pr-4 py-3 rounded-xl border border-ocean/50 bg-navy/80 focus:bg-navy focus:ring-2 focus:ring-steel/50 focus:border-steel transition-all text-offwhite text-lg placeholder-ice/40"
                      />
                    </div>
                    {errors.location && <p className="text-red-400 text-sm mt-1.5">{errors.location.message}</p>}
                  </div>
                </div>

                {isAtLimit ? (
                  <div className="bg-rose-500/10 p-4 rounded-xl border border-rose-500/30 flex items-start gap-3">
                    <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
                    <div>
                      <p className="text-sm text-rose-300 font-semibold">Daily search limit reached</p>
                      <p className="text-xs text-rose-400/80 mt-1">You've used all {searchesPerDay} searches today. Upgrade your plan or wait until tomorrow.</p>
                      <Link href="/dashboard/billing" className="text-xs text-steel hover:underline mt-2 inline-block">Upgrade Plan →</Link>
                    </div>
                  </div>
                ) : (
                  <div className="bg-steel/10 p-4 rounded-xl border border-steel/20 flex items-start gap-3">
                    <Sparkles className="w-5 h-5 text-steel shrink-0 mt-0.5" />
                    <p className="text-sm text-ice/80 leading-relaxed">
                      Hyperclients will scrape Google Maps for <span className="font-semibold px-1 text-offwhite">up to 50 targeted</span> results, extract websites, and run them through our AI analyzer. The process usually takes 2-10 minutes depending on the city.
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
                    variant={isAtLimit ? "outline" : "gradient"}
                    className="text-lg py-4 px-8"
                    disabled={isAtLimit}
                  >
                    <SearchIcon className="w-5 h-5" />
                    Start Search
                  </LoadingButton>
                </div>
              </form>
            </GlassCard>
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
                  <Users className="w-5 h-5 text-steel" />
                  <h2 className="text-lg font-bold text-offwhite tracking-tight">Live Results</h2>
                </div>
                <span className="text-sm text-ice/60 font-medium">
                  {results.length}{resultsTotal > results.length ? ` / ${resultsTotal}` : ''} found
                </span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {results.map((lead, idx) => (
                  <LiveResultCard key={lead.id} lead={lead} index={idx} />
                ))}
              </div>
              {!isSearchActive && resultsTotal > 0 && (
                <div className="flex justify-center mt-6 gap-4">
                  <Link
                    href="/dashboard/leads"
                    className="inline-flex items-center justify-center px-6 py-2.5 font-semibold rounded-xl text-offwhite bg-gradient-to-r from-steel to-ocean hover:from-steel/90 hover:to-ocean/90 transition-all shadow-[0_0_20px_rgba(74,127,167,0.4)] hover:shadow-[0_0_30px_rgba(74,127,167,0.6)]"
                  >
                    View All Leads in Dashboard
                  </Link>
                  <button
                    onClick={() => { clearActiveSearch(); }}
                    className="inline-flex items-center justify-center px-6 py-2.5 font-semibold rounded-xl text-steel border border-steel/40 hover:bg-steel/10 transition-all"
                  >
                    New Search
                  </button>
                </div>
              )}
            </>
          )}
          {!isSearchActive && progress && ['completed', 'failed', 'cancelled'].includes(progress.status) && (
            <div className="flex justify-center mt-6">
              <button
                onClick={() => { clearActiveSearch(); }}
                className="inline-flex items-center justify-center px-6 py-2.5 font-semibold rounded-xl text-steel border border-steel/40 hover:bg-steel/10 transition-all"
              >
                New Search
              </button>
            </div>
          )}
        </motion.div>
      )}
    </div>
  );
}
