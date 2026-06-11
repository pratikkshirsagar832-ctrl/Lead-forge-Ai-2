'use client';

import { motion } from 'framer-motion';

const steps = [
  {
    number: '01',
    title: 'Enter Niche & Location',
    description: 'Tell us exactly who you are looking for. E.g., "Plumbers in Dallas, TX" or "Dentists in London".',
  },
  {
    number: '02',
    title: 'Auto-Scrape Engine',
    description: 'Our backend connects directly to Google Maps, fetching up to 50 targeted businesses and extracting their core info and websites.',
  },
  {
    number: '03',
    title: 'Smart AI Analysis',
    description: 'We visit every website found to check for load speed, content quality, and basic SEO issues, categorizing them instantly.',
  },
  {
    number: '04',
    title: 'Personalized Pitch',
    description: 'Use our AI to write a highly customized email draft referencing specific issues on their website to dramatically increase reply rates.',
  },
];

export function HowItWorks() {
  return (
    <section id="how-it-works" className="py-24 bg-navy relative overflow-hidden">
      <div className="absolute -top-40 -left-40 w-[600px] h-[600px] rounded-full bg-ocean/10 blur-[120px] pointer-events-none" />
      <div className="absolute -bottom-40 -right-40 w-[500px] h-[500px] rounded-full bg-steel/10 blur-[100px] pointer-events-none" />
      
      <div className="container mx-auto px-6 lg:px-8 relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mb-16"
        >
          <span className="text-steel font-semibold tracking-wide uppercase text-sm mb-3 block">Simple Pipeline</span>
          <h2 className="text-3xl md:text-5xl font-bold text-offwhite mb-6 tracking-tight">How it works</h2>
          <p className="text-lg text-ice/70 max-w-2xl">
            A linear pipeline built for speed and quality. Go from a simple search query to a qualified list of prospects in minutes.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 relative">
          <div className="hidden lg:block absolute top-12 left-[12%] right-[12%] h-px bg-gradient-to-r from-steel/40 via-ice/20 to-steel/40 pointer-events-none" />
          
          {steps.map((step, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: idx * 0.15 }}
              className="relative group"
            >
              <div className="flex items-center lg:block">
                <div className="text-7xl font-black text-ocean/50 mb-6 group-hover:text-steel/40 transition-colors duration-500">
                  {step.number}
                </div>
                <div className="lg:mt-4">
                  <h4 className="text-xl font-bold text-offwhite mb-3 group-hover:text-steel transition-colors duration-300">
                    {step.title}
                  </h4>
                  <p className="text-ice/60 leading-relaxed">
                    {step.description}
                  </p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
