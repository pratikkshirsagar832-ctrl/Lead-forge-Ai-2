'use client';

import { motion } from 'framer-motion';
import { Map, Bot, Zap, Filter, LayoutDashboard, Target, Sparkles } from 'lucide-react';

const features = [
  {
    icon: <Map className="w-6 h-6 text-steel" />,
    title: 'Google Maps Scraping',
    description: 'Instantly extract hundreds of local businesses in any niche and location directly from Google Maps.',
    gradient: 'from-steel/20 to-ocean/20',
  },
  {
    icon: <Sparkles className="w-6 h-6 text-ice" />,
    title: 'Automated Website Analysis',
    description: 'We visit their website, analyze it for quality, and categorize the lead as Hot, Warm, or Skip based on your criteria.',
    gradient: 'from-ice/20 to-steel/20',
  },
  {
    icon: <Zap className="w-6 h-6 text-steel" />,
    title: 'AI Pitch Generation',
    description: 'Generate hyper-personalized outreach pitches based on the business\'s website context and missing features.',
    gradient: 'from-steel/20 to-ocean/20',
  },
  {
    icon: <Filter className="w-6 h-6 text-ice" />,
    title: 'Smart Filtering',
    description: 'Quickly sort and filter your leads by category, rating, review count, and website status.',
    gradient: 'from-ice/20 to-steel/20',
  },
  {
    icon: <LayoutDashboard className="w-6 h-6 text-steel" />,
    title: 'Built-in CRM',
    description: 'Track contact status, leave notes, favorite leads, and monitor your entire pipeline in one clean dashboard.',
    gradient: 'from-steel/20 to-ocean/20',
  },
  {
    icon: <Target className="w-6 h-6 text-ice" />,
    title: 'Instant CSV Export',
    description: 'Export your qualified list to CSV with one click, ready to import into Instantly, Lemlist, or any cold email tool.',
    gradient: 'from-ice/20 to-steel/20',
  },
];

export function Features() {
  return (
    <section id="features" className="py-24 bg-navy relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-b from-ocean/10 via-transparent to-ocean/10 pointer-events-none" />
      <div className="container mx-auto px-6 lg:px-8 relative z-10">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <motion.span
            initial={{ opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-steel font-semibold tracking-wide uppercase text-sm mb-3 block"
          >
            Powerful Features
          </motion.span>
          <motion.h3
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
            className="text-3xl md:text-5xl font-bold text-offwhite mb-6 tracking-tight"
          >
            Everything you need to scale output
          </motion.h3>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
            className="text-lg text-ice/70"
          >
            Stop switching between different tools. LeadForge AI combines map scraping, website analysis, AI personalization, and CRM tracking into one seamless workflow.
          </motion.p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-7xl mx-auto">
          {features.map((feature, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-50px' }}
              transition={{ duration: 0.5, delay: idx * 0.1 }}
              className="p-8 rounded-2xl border border-ocean/40 hover:border-steel/50 hover:shadow-xl hover:shadow-steel/5 transition-all bg-gradient-to-br from-ocean/20 to-navy group relative overflow-hidden"
            >
              <div className="absolute inset-0 bg-gradient-to-br opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" style={{ background: `radial-gradient(circle at 50% 0%, ${feature.gradient}), transparent` }} />
              <div className="relative z-10">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-steel/20 to-ice/20 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform group-hover:shadow-lg group-hover:shadow-steel/20">
                  {feature.icon}
                </div>
                <h4 className="text-xl font-bold text-offwhite mb-3">{feature.title}</h4>
                <p className="text-ice/70 leading-relaxed">
                  {feature.description}
                </p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
