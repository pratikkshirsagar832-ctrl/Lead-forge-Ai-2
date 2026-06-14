'use client';

import { forwardRef, ReactNode } from 'react';
import { cn } from '@/lib/utils';
import { motion, HTMLMotionProps } from 'framer-motion';

interface GlassCardProps extends HTMLMotionProps<'div'> {
  hoverEffect?: boolean;
  glowBorder?: boolean;
  children?: ReactNode;
  elevation?: 1 | 2 | 3 | 4;
  delay?: number;
}

export const GlassCard = forwardRef<HTMLDivElement, GlassCardProps>(
  ({ className, hoverEffect = false, glowBorder = false, elevation, delay = 0, children, ...props }, ref) => {
    return (
      <motion.div
        ref={ref}
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay, ease: [0.25, 0.1, 0.25, 1] }}
        whileHover={hoverEffect ? {
          y: -3,
          boxShadow: '0 16px 48px -8px rgba(10, 25, 49, 0.5), 0 0 0 1px rgba(74, 127, 167, 0.25)',
          transition: { duration: 0.25, ease: 'easeOut' },
        } : undefined}
        className={cn(
          'relative group overflow-hidden rounded-2xl bg-gradient-to-br from-ocean/35 to-navy/80 border border-ocean/30 shadow-lg shadow-navy/30 transition-shadow duration-300',
          glowBorder && 'animate-border-glow',
          elevation === 1 && 'elevation-1',
          elevation === 2 && 'elevation-2',
          elevation === 3 && 'elevation-3',
          elevation === 4 && 'elevation-4',
          className
        )}
        {...props}
      >
        <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-steel/40 to-transparent pointer-events-none" />
        <div className="absolute inset-x-0 bottom-0 h-px bg-gradient-to-r from-transparent via-steel/10 to-transparent pointer-events-none" />
        {hoverEffect && (
          <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 bg-gradient-to-br from-steel/[0.03] to-transparent pointer-events-none" />
        )}
        {children}
      </motion.div>
    );
  }
);

GlassCard.displayName = 'GlassCard';
