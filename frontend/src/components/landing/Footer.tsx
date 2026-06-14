import Link from 'next/link';
import { Target } from 'lucide-react';

export function Footer() {
  return (
    <footer className="bg-navy py-16 text-ice/60 border-t border-ocean/30">
      <div className="container mx-auto px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-12 mb-12 border-b border-ocean/30 pb-12">
          <div className="md:col-span-2">
            <Link href="/" className="flex items-center gap-2 mb-6 text-offwhite w-fit">
              <div className="bg-steel rounded-lg p-1">
                <Target className="w-5 h-5 text-offwhite" />
              </div>
              <span className="font-bold text-xl tracking-tight">Hyperclients</span>
            </Link>
            <p className="max-w-xs leading-relaxed text-sm text-ice/60">
              The automated lead generation engine built for agency owners, freelancers, and B2B founders.
            </p>
          </div>

          <div>
            <h4 className="text-offwhite font-semibold mb-4">Product</h4>
            <ul className="space-y-3 text-sm">
              <li><Link href="#features" className="hover:text-steel transition-colors">Features</Link></li>
              <li><Link href="#how-it-works" className="hover:text-steel transition-colors">How it Works</Link></li>
              <li><Link href="/dashboard" className="hover:text-steel transition-colors">Dashboard</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="text-offwhite font-semibold mb-4">Legal</h4>
            <ul className="space-y-3 text-sm">
              <li><Link href="#" className="hover:text-steel transition-colors">Privacy Policy</Link></li>
              <li><Link href="#" className="hover:text-steel transition-colors">Terms of Service</Link></li>
            </ul>
          </div>
        </div>

        <div className="flex flex-col md:flex-row items-center justify-between text-sm">
          <p>© {new Date().getFullYear()} Hyperclients. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
}
