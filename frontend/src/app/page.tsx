import { Metadata } from 'next';
import Image from 'next/image';
import { Hero } from '@/components/landing/Hero';
import { Features } from '@/components/landing/Features';
import { HowItWorks } from '@/components/landing/HowItWorks';
import { Footer } from '@/components/landing/Footer';
import { ThemeToggle } from '@/components/ThemeToggle';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'Hyperclients | Automated Lead Generation & AI Pitch Engine',
  description: 'Find perfect clients on Google Maps in minutes. Extract businesses, analyze websites, and draft personalized pitches automatically.',
};

export default function LandingPage() {
  return (
    <div className="min-h-screen flex flex-col font-sans selection:bg-violet/30 selection:text-offwhite">
      <header className="fixed top-0 inset-x-0 z-50 bg-navy/80 backdrop-blur-md border-b border-ocean/30">
        <div className="container mx-auto px-6 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2 group">
            <div className="bg-gradient-to-br from-violet to-steel rounded-lg p-1 group-hover:scale-105 transition-transform duration-300 shadow-lg shadow-violet/20">
              <Image src="/hyperclients-logo.png" alt="Hyperclients" width={40} height={40} className="object-contain" />
            </div>
            <span className="font-bold text-xl tracking-tight text-offwhite" style={{ fontFamily: 'var(--font-heading)' }}>Hyperclients</span>
          </Link>

          <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-ice/70">
            <Link href="#features" className="hover:text-offwhite transition-colors duration-200">Features</Link>
            <Link href="#how-it-works" className="hover:text-offwhite transition-colors duration-200">How it Works</Link>
          </nav>

          <div className="flex items-center gap-4">
            <ThemeToggle />
            <Link
              href="/dashboard"
              className="text-sm font-medium bg-gradient-to-r from-cta to-cta-light text-white px-5 py-2.5 rounded-lg hover:shadow-lg hover:shadow-cta/20 hover:scale-[1.03] active:scale-[0.97] transition-all duration-200"
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
