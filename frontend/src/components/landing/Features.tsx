'use client';

import { motion } from 'framer-motion';
import { Map, Bot, Zap, Filter, LayoutDashboard, Target, Sparkles } from 'lucide-react';

const features = [
  {
    icon: <Map className="w-6 h-6" />,
    title: 'Google Maps Scraping',
    description: 'Instantly extract hundreds of local businesses in any niche and location directly from Google Maps.',
    iconBg: 'from-violet-400/20 to-steel/20',
    iconColor: 'text-violet-400',
  },
  {
    icon: <Sparkles className="w-6 h-6" />,
    title: 'Automated Website Analysis',
    description: 'We visit their website, analyze it for quality, and identify the best opportunities for you.',
    iconBg: 'from-amber-400/20 to-steel/20',
    iconColor: 'text-amber-400',
  },
  {
    icon: <Zap className="w-6 h-6" />,
    title: 'AI Pitch Generation',
    description: 'Generate hyper-personalized outreach pitches based on the business website context and missing features.',
    iconBg: 'from-cta-light/20 to-steel/20',
    iconColor: 'text-cta-light',
  },
  {
    icon: <Filter className="w-6 h-6" />,
    title: 'Smart Filtering',
    description: 'Quickly sort and filter your leads by category, rating, review count, and website status.',
    iconBg: 'from-emerald-400/20 to-steel/20',
    iconColor: 'text-emerald-400',
  },
  {
    icon: <LayoutDashboard className="w-6 h-6" />,
    title: 'Built-in CRM',
    description: 'Track contact status, leave notes, favorite leads, and monitor your entire pipeline in one clean dashboard.',
    iconBg: 'from-steel/20 to-ocean/20',
    iconColor: 'text-steel',
  },
  {
    icon: <Target className="w-6 h-6" />,
    title: 'Instant CSV Export',
    description: 'Export your qualified list to CSV with one click, ready to import into any cold email tool.',
    iconBg: 'from-rose-400/20 to-steel/20',
    iconColor: 'text-rose-400',
  },
];

const cardVariants = {
  hidden: { opacity: 0, y: 24 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, delay: i * 0.08, ease: [0.25, 0.1, 0.25, 1] as [number, number, number, number] },
  }),
};

export function Features() {
  return (
    <section id="features" className="py-24 bg-navy relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-b from-violet/5 via-transparent to-ocean/5 pointer-events-none" />
      <div className="container mx-auto px-6 lg:px-8 relative z-10">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <motion.span
            initial={{ opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-violet-400 font-semibold tracking-wide uppercase text-sm mb-3 block"
          >
            Powerful Features
          </motion.span>
          <motion.h3
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
            className="text-3xl md:text-5xl font-bold text-offwhite mb-6 tracking-tight"
            style={{ fontFamily: 'var(--font-heading)' }}
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
            Stop switching between different tools. Hyperclients combines map scraping, website analysis,
            AI personalization, and CRM tracking into one seamless workflow.
          </motion.p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-7xl mx-auto">
          {features.map((feature, idx) => (
            <motion.div
              key={idx}
              custom={idx}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, margin: '-50px' }}
              variants={cardVariants}
              className="group relative p-8 rounded-2xl border border-ocean/40 hover:border-steel/50 transition-all duration-300 bg-gradient-to-br from-ocean/20 to-navy/90 hover:shadow-xl hover:shadow-steel/5"
            >
              <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-violet/5 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />
              <div className="relative z-10">
                <div
                  className={`w-12 h-12 rounded-xl bg-gradient-to-br ${feature.iconBg} flex items-center justify-center mb-6 group-hover:scale-110 group-hover:shadow-lg transition-all duration-300 ${feature.iconColor}`}
                >
                  {feature.icon}
                </div>
                <h4 className="text-xl font-bold text-offwhite mb-3 group-hover:text-offwhite transition-colors" style={{ fontFamily: 'var(--font-heading)' }}>
                  {feature.title}
                </h4>
                <p className="text-ice/70 leading-relaxed group-hover:text-ice/80 transition-colors">
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
