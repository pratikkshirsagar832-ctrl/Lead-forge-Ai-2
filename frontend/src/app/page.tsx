import { Metadata } from 'next';
import { Hero } from '@/components/landing/Hero';
import { Features } from '@/components/landing/Features';
import { HowItWorks } from '@/components/landing/HowItWorks';
import { Footer } from '@/components/landing/Footer';
import { ThemeToggle } from '@/components/ThemeToggle';
import Link from 'next/link';
import { Target } from 'lucide-react';

export const metadata: Metadata = {
  title: 'LeadForge AI | Automated Lead Generation & AI Pitch Engine',
  description: 'Find perfect clients on Google Maps in minutes. Extract businesses, analyze websites, and draft personalized pitches automatically.',
};

export default function LandingPage() {
  return (
    <div className="min-h-screen flex flex-col font-sans selection:bg-steel/30 selection:text-ice">
      <header className="fixed top-0 inset-x-0 z-50 bg-navy/80 backdrop-blur-md border-b border-ocean/30">
        <div className="container mx-auto px-6 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2 group">
            <div className="bg-steel rounded-lg p-1.5 group-hover:scale-105 transition-transform duration-300">
              <Target className="w-5 h-5 text-offwhite" />
            </div>
            <span className="font-bold text-xl tracking-tight text-offwhite">LeadForge AI</span>
          </Link>

          <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-ice/70">
            <Link href="#features" className="hover:text-offwhite transition-colors">Features</Link>
            <Link href="#how-it-works" className="hover:text-offwhite transition-colors">How it Works</Link>
          </nav>

          <div className="flex items-center gap-4">
            <ThemeToggle />
            <Link
              href="/dashboard"
              className="text-sm font-medium bg-steel text-offwhite px-4 py-2 rounded-lg hover:bg-steel/80 transition-colors"
            >
              Dashboard
            </Link>
          </div>
        </div>
      </header>

      <main className="flex-1">
        <Hero />
        <Features />
        <HowItWorks />
      </main>

      <Footer />
    </div>
  );
}
