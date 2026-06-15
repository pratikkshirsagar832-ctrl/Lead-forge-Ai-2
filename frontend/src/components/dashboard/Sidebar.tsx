'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import Image from 'next/image';
import { cn } from '@/lib/utils';
import { supabase } from '@/lib/supabase';
import api from '@/lib/api';
import {
  LayoutDashboard,
  Search,
  Users,
  History,
  Download,
  Settings,
  Target,
  X,
  CreditCard,
  LogOut,
  User,
  Zap,
} from 'lucide-react';
import { ThemeToggle } from '@/components/ThemeToggle';

const navItems = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'New Search', href: '/dashboard/search', icon: Search },
  { name: 'Leads', href: '/dashboard/leads', icon: Users },
  { name: 'History', href: '/dashboard/history', icon: History },
  { name: 'Export', href: '/dashboard/export', icon: Download },
  { name: 'Billing', href: '/dashboard/billing', icon: CreditCard },
  { name: 'Settings', href: '/dashboard/settings', icon: Settings },
];

export function Sidebar({ open, onClose }: { open: boolean; onClose: () => void }) {
  const pathname = usePathname();
  const [user, setUser] = useState<any>(null);
  const [subscription, setSubscription] = useState<any>(null);

  useEffect(() => {
    const fetchUser = async () => {
      const { data: { user: u } } = await supabase.auth.getUser();
      if (u) setUser(u);

      try {
        const resp = await api.get('/api/auth/me');
        if (resp.data?.subscription) {
          setSubscription(resp.data.subscription);
        }
      } catch (e) {
        console.error('Failed to fetch subscription:', e);
      }
    };
    fetchUser();
  }, []);

  const handleLogout = async () => {
    await supabase.auth.signOut();
    window.location.href = '/login';
  };

  const planBadge = subscription?.plan_name || 'Free';
  const planColor = planBadge === 'Pro' ? 'bg-violet/20 text-violet border-violet/30'
    : planBadge === 'Agency' ? 'text-amber-400 bg-amber-500/10 border-amber-500/30'
    : planBadge === 'Solo' ? 'text-sky-400 bg-sky-500/10 border-sky-500/30'
    : 'text-ice/60 bg-ocean/20 border-ocean/30';

  const remaining = subscription?.remaining_searches ?? 1;
  const searchesPerDay = subscription?.searches_per_day ?? 1;
  const leadsRemaining = subscription?.remaining_leads ?? 0;
  const leadsPerDay = subscription?.leads_per_day ?? 30;

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
            <div className="bg-gradient-to-br from-violet to-steel rounded-lg p-1 group-hover:scale-105 transition-transform duration-300 shadow-lg shadow-violet/20">
              <Image src="/hyperclients-logo.png" alt="Hyperclients" width={40} height={40} className="object-contain" />
            </div>
            <span className="font-bold text-xl tracking-tight text-offwhite" style={{ fontFamily: 'var(--font-heading)' }}>Hyperclients</span>
          </Link>
          <button onClick={onClose} className="lg:hidden p-1.5 rounded-lg hover:bg-ocean/50 text-ice/60 hover:text-offwhite transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <nav className="flex-1 px-4 py-2 space-y-1 overflow-y-auto">
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

        {/* User section */}
        <div className="p-4 border-t border-ocean/40 space-y-3">
          <div className="flex items-center gap-3 px-2">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-violet to-steel flex items-center justify-center text-xs font-bold text-offwhite shrink-0 overflow-hidden">
              <img
                src={`https://ui-avatars.com/api/?name=${encodeURIComponent(user?.email || 'U')}&background=6366f1&color=fff&size=32&bold=true`}
                alt=""
                className="w-full h-full object-cover"
              />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-semibold text-offwhite truncate">{user?.email || 'User'}</p>
              <span className={cn('text-[10px] font-medium px-1.5 py-0.5 rounded border', planColor)}>
                {planBadge === 'Free' && subscription?.is_trial_expired ? 'Trial Expired' : planBadge}
              </span>
            </div>
          </div>

          {searchesPerDay > 0 && (
            <div className="px-2">
              <div className="flex justify-between text-[10px] text-ice/50 mb-1">
                <span>Searches today</span>
                <span>{remaining}/{searchesPerDay}</span>
              </div>
              <div className="h-1.5 rounded-full bg-ocean/30 overflow-hidden">
                <div
                  className={cn('h-full rounded-full transition-all', remaining > 0 ? 'bg-steel' : 'bg-rose-500')}
                  style={{ width: `${Math.min(100, ((searchesPerDay - remaining) / searchesPerDay) * 100)}%` }}
                />
              </div>
            </div>
          )}
          {leadsPerDay > 0 && (
            <div className="px-2">
              <div className="flex justify-between text-[10px] text-ice/50 mb-1">
                <span>Leads today</span>
                <span>{leadsPerDay - leadsRemaining}/{leadsPerDay}</span>
              </div>
              <div className="h-1.5 rounded-full bg-ocean/30 overflow-hidden">
                <div
                  className={cn('h-full rounded-full transition-all', leadsRemaining > 0 ? 'bg-emerald-500' : 'bg-rose-500')}
                  style={{ width: `${Math.min(100, ((leadsPerDay - leadsRemaining) / leadsPerDay) * 100)}%` }}
                />
              </div>
            </div>
          )}

          <div className="flex items-center justify-between px-2">
            <button
              onClick={handleLogout}
              className="flex items-center gap-1.5 text-[11px] text-ice/40 hover:text-rose-400 transition-colors"
            >
              <LogOut className="w-3.5 h-3.5" />
              Sign Out
            </button>
            <ThemeToggle />
          </div>
        </div>
      </div>
    </>
  );
}
