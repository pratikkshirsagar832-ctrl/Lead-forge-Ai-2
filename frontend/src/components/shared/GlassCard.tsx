'use client';

import { forwardRef, ReactNode } from 'react';
import { cn } from '@/lib/utils';
import { motion, HTMLMotionProps } from 'framer-motion';

interface GlassCardProps extends HTMLMotionProps<'div'> {
  hoverEffect?: boolean;
  glowBorder?: boolean;
  children?: ReactNode;
}

export const GlassCard = forwardRef<HTMLDivElement, GlassCardProps>(
  ({ className, hoverEffect = false, glowBorder = false, children, ...props }, ref) => {
    return (
      <motion.div
        ref={ref}
        whileHover={hoverEffect ? {
          y: -3,
          boxShadow: '0 12px 48px -8px rgba(10, 25, 49, 0.4), 0 0 0 1px rgba(74, 127, 167, 0.2)',
          transition: { duration: 0.2 },
        } : undefined}
        className={cn(
          'relative group overflow-hidden rounded-2xl bg-gradient-to-br from-ocean/35 to-navy/80 border border-ocean/30 shadow-lg shadow-navy/30 transition-all duration-300',
          glowBorder && 'animate-border-glow',
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
