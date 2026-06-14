'use client';

import { motion } from 'framer-motion';
import { ArrowRight, Zap, Target, Sparkles } from 'lucide-react';
import Link from 'next/link';

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.12, delayChildren: 0.1 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: [0.25, 0.1, 0.25, 1] } },
};

export function Hero() {
  return (
    <div className="relative overflow-hidden bg-navy min-h-screen pt-[120px]">
      <div className="absolute top-1/4 -left-32 w-96 h-96 bg-violet/5 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 -right-32 w-96 h-96 bg-cta/5 rounded-full blur-3xl pointer-events-none" />

      <div className="container relative z-10 mx-auto px-6 lg:px-8">
        <motion.div
          className="mx-auto max-w-4xl text-center"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          <motion.div variants={itemVariants}>
            <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-gradient-to-r from-violet/20 to-steel/20 text-ice text-sm font-semibold mb-6 border border-violet/30 shadow-lg shadow-violet/5">
              <Sparkles className="w-4 h-4 text-violet-400" />
              Hyperclients is live
            </span>
          </motion.div>

          <motion.h1
            variants={itemVariants}
            className="text-5xl md:text-7xl font-extrabold tracking-tight text-offwhite mb-8 leading-tight"
            style={{ fontFamily: 'var(--font-heading)' }}
          >
            Find perfect clients on{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-violet-400 via-steel to-ice">
              Google Maps
            </span>
            <br className="select-none hidden md:block" />
            in minutes.
          </motion.h1>

          <motion.p
            variants={itemVariants}
            className="text-xl md:text-2xl text-ice/70 mb-10 max-w-3xl mx-auto leading-relaxed"
          >
            Stop wasting hours manually searching. Hyperclients automatically extracts businesses, analyzes their websites, and drafts personalized pitches.
          </motion.p>

          <motion.div
            variants={itemVariants}
            className="flex flex-col sm:flex-row items-center justify-center gap-4"
          >
            <Link
              href="/dashboard"
              className="group w-full sm:w-auto px-8 py-4 bg-gradient-to-r from-cta to-cta-light text-white rounded-xl font-semibold text-lg hover:shadow-xl hover:shadow-cta/25 hover:scale-[1.03] active:scale-[0.97] transition-all duration-200 flex items-center justify-center gap-2"
            >
              Go to Dashboard <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </Link>
            <Link
              href="#features"
              className="w-full sm:w-auto px-8 py-4 bg-gradient-to-r from-ocean/50 to-navy text-ice border border-ocean/50 rounded-xl font-semibold text-lg hover:bg-ocean/60 hover:border-steel/50 active:scale-[0.97] transition-all duration-200"
            >
              How it works
            </Link>
          </motion.div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.5, ease: [0.25, 0.1, 0.25, 1] }}
          className="mt-20 mx-auto max-w-6xl relative"
        >
          <div className="rounded-2xl border border-ocean/60 bg-navy/50 p-2 shadow-2xl shadow-steel/10 backdrop-blur-sm overflow-hidden ring-1 ring-steel/20">
            <div className="rounded-xl border border-ocean/30 bg-navy/80 p-4 shadow-sm overflow-hidden h-[400px] md:h-[600px] relative">
              <div className="flex items-center justify-between border-b border-ocean/30 pb-4 mb-6">
                <div className="flex items-center gap-4">
                  <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-steel/40 to-ocean/40 flex items-center justify-center">
                    <Target className="w-4 h-4 text-offwhite" />
                  </div>
                  <div className="h-5 w-40 bg-gradient-to-r from-ocean/60 to-ocean/30 rounded" />
                </div>
                <div className="flex gap-2">
                  <div className="h-8 w-24 bg-ocean/50 rounded-md" />
                  <div className="h-8 w-8 bg-ocean/50 rounded-md" />
                </div>
              </div>

              <div className="space-y-4">
                <div className="flex items-center gap-4 bg-gradient-to-r from-ocean/30 to-ocean/10 p-4 rounded-lg">
                  <div className="h-6 w-1/4 bg-ice/20 rounded" />
                  <div className="h-6 w-1/4 bg-ice/20 rounded" />
                  <div className="h-6 w-1/4 bg-ice/20 rounded" />
                  <div className="h-6 w-1/4 bg-ice/20 rounded" />
                </div>
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="flex items-center gap-4 p-4 border-b border-ocean/20">
                    <div className="h-5 w-1/4 bg-ocean/40 rounded" />
                    <div className="flex items-center gap-2 w-1/4">
                      <div className="h-5 w-5 bg-gradient-to-br from-steel/30 to-ice/20 rounded-full" />
                      <div className="h-5 w-20 bg-ocean/40 rounded" />
                    </div>
                    <div className="h-5 w-1/4 bg-ocean/40 rounded" />
                    <div className="h-6 w-16 bg-emerald-500/20 rounded-full" />
                  </div>
                ))}
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
