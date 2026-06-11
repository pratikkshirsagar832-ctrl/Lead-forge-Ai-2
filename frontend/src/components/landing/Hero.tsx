'use client';

import { motion } from 'framer-motion';
import { ArrowRight, Zap, Target } from 'lucide-react';
import Link from 'next/link';
export function Hero() {
  return (
    <div className="relative overflow-hidden bg-navy min-h-screen pt-[120px]">
      
      <div className="container relative z-10 mx-auto px-6 lg:px-8">
        <div className="mx-auto max-w-4xl text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-steel/20 text-ice text-sm font-semibold mb-6 border border-steel/30">
              <Zap className="w-4 h-4 text-steel" />
              LeadForge AI v2.0 is live
            </span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="text-5xl md:text-7xl font-extrabold tracking-tight text-offwhite mb-8 leading-tight"
          >
            Find perfect clients on{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-steel to-ice">Google Maps</span>
            <br className="select-none hidden md:block" />
            in minutes.
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="text-xl md:text-2xl text-ice/70 mb-10 max-w-3xl mx-auto leading-relaxed"
          >
            Stop wasting hours manually searching. LeadForge AI automatically extracts businesses, analyzes their websites, and drafts personalized pitches.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4"
          >
            <Link
              href="/dashboard"
              className="w-full sm:w-auto px-8 py-4 bg-gradient-to-r from-steel to-ocean text-offwhite rounded-xl font-semibold text-lg hover:from-steel/90 hover:to-ocean/90 hover:shadow-lg hover:shadow-steel/30 active:scale-95 transition-all flex items-center justify-center gap-2"
            >
              Go to Dashboard <ArrowRight className="w-5 h-5" />
            </Link>
            <Link
              href="#how-it-works"
              className="w-full sm:w-auto px-8 py-4 bg-ocean text-ice border border-steel/30 rounded-xl font-semibold text-lg hover:bg-ocean/80 active:scale-95 transition-all"
            >
              How it works
            </Link>
          </motion.div>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.5 }}
          className="mt-20 mx-auto max-w-6xl relative"
        >
          <div className="rounded-2xl border border-ocean/60 bg-navy/50 p-2 shadow-2xl shadow-steel/10 backdrop-blur-sm overflow-hidden ring-1 ring-steel/20">
            <div className="rounded-xl border border-ocean/30 bg-navy/80 p-4 shadow-sm overflow-hidden h-[400px] md:h-[600px] relative">
              <div className="flex items-center justify-between border-b border-ocean/30 pb-4 mb-6">
                <div className="flex items-center gap-4">
                  <div className="w-8 h-8 rounded-lg bg-steel/20 flex items-center justify-center">
                    <Target className="w-4 h-4 text-steel" />
                  </div>
                  <div className="h-5 w-40 bg-ocean/50 rounded" />
                </div>
                <div className="flex gap-2">
                  <div className="h-8 w-24 bg-ocean/50 rounded-md" />
                  <div className="h-8 w-8 bg-ocean/50 rounded-md" />
                </div>
              </div>

              <div className="space-y-4">
                <div className="flex items-center gap-4 bg-ocean/30 p-4 rounded-lg">
                  <div className="h-6 w-1/4 bg-ice/20 rounded" />
                  <div className="h-6 w-1/4 bg-ice/20 rounded" />
                  <div className="h-6 w-1/4 bg-ice/20 rounded" />
                  <div className="h-6 w-1/4 bg-ice/20 rounded" />
                </div>
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="flex items-center gap-4 p-4 border-b border-ocean/20">
                    <div className="h-5 w-1/4 bg-ocean/40 rounded" />
                    <div className="flex items-center gap-2 w-1/4">
                      <div className="h-5 w-5 bg-steel/20 rounded-full" />
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
