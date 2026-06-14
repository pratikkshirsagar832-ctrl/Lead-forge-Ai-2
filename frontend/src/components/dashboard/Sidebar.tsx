'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { 
  LayoutDashboard, 
  Search, 
  Users, 
  History, 
  Download, 
  Settings,
  Target,
  X,
} from 'lucide-react';
import { ThemeToggle } from '@/components/ThemeToggle';

const navItems = [
  { name: 'Overview', href: '/dashboard', icon: LayoutDashboard },
  { name: 'New Search', href: '/dashboard/search', icon: Search },
  { name: 'Leads', href: '/dashboard/leads', icon: Users },
  { name: 'History', href: '/dashboard/history', icon: History },
  { name: 'Export', href: '/dashboard/export', icon: Download },
  { name: 'Settings', href: '/dashboard/settings', icon: Settings },
];

export function Sidebar({ open, onClose }: { open: boolean; onClose: () => void }) {
  const pathname = usePathname();

  return (
    <>
      {open && (
        <div className="fixed inset-0 bg-navy/70 backdrop-blur-sm z-20 lg:hidden" onClick={onClose} />
      )}
      <div className={cn(
        'w-64 bg-gradient-to-b from-navy to-ocean/20 flex flex-col h-screen fixed top-0 left-0 border-r border-ocean/40 shrink-0 z-30 transition-transform duration-300 backdrop-blur-sm',
        'lg:translate-x-0',
        open ? 'translate-x-0' : '-translate-x-full'
      )}>
        <div className="p-6 flex items-center justify-between">
          <Link href="/dashboard" className="flex items-center gap-2 group" onClick={onClose}>
            <div className="bg-gradient-to-br from-violet to-steel rounded-lg p-1.5 group-hover:scale-105 transition-transform duration-300 shadow-lg shadow-violet/20">
              <Target className="w-5 h-5 text-offwhite" />
            </div>
            <span className="font-bold text-xl tracking-tight text-offwhite" style={{ fontFamily: 'var(--font-heading)' }}>Hyperclients</span>
          </Link>
          <button onClick={onClose} className="lg:hidden p-1.5 rounded-lg hover:bg-ocean/50 text-ice/60 hover:text-offwhite transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <nav className="flex-1 px-4 py-4 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const isActive = pathname === item.href || (item.href !== '/dashboard' && pathname.startsWith(item.href));
            return (
              <Link
                key={item.name}
                href={item.href}
                onClick={onClose}
                className={cn(
                  'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all group',
                  isActive 
                    ? 'bg-steel text-offwhite shadow-lg shadow-steel/20' 
                    : 'text-ice/60 hover:text-offwhite hover:bg-ocean/50'
                )}
              >
                <item.icon className={cn('w-5 h-5', isActive ? 'text-ice' : 'text-steel group-hover:text-ice')} />
                {item.name}
              </Link>
            );
          })}
        </nav>

      <div className="p-4 border-t border-ocean/40">
        <div className="flex items-center justify-center">
          <ThemeToggle />
        </div>
      </div>
    </div>
    </>
  );
}
