import { StatsCards } from '@/components/dashboard/StatsCards';
import { GlassCard } from '@/components/shared/GlassCard';
import { Rocket, Target, Users } from 'lucide-react';
import Link from 'next/link';

export const metadata = {
  title: 'Overview | LeadForge AI',
};

export default function DashboardOverview() {
  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div>
        <h1 className="text-3xl font-bold text-offwhite tracking-tight">Overview</h1>
        <p className="text-ice/60 mt-2">Welcome to LeadForge. Here&apos;s what&apos;s happening today.</p>
      </div>

      <StatsCards />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <GlassCard className="col-span-1 lg:col-span-2 p-8 bg-gradient-to-br from-steel to-ocean text-offwhite border-0 shadow-lg shadow-steel/20 relative overflow-hidden">
          <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjQwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNMjg4IDE5MkMyODggMjY1LjYgMjI5LjYgMzI0IDE1NiAzMjRDODIuNCAzMjQgMjQgMjY1LjYgMjQgMTkyQzI0IDExOC40IDgyLjQgNjAgMTU2IDYwQzIyOS42IDYwIDI4OCAxMTguNCAyODggMTkyWiIgZmlsbD0icmdiYSgyNTUsMjU1LDI1NSwwLjA1KSIvPjwvc3ZnPg==')] opacity-20 pointer-events-none" />
          <div className="max-w-md relative z-10">
            <h2 className="text-2xl font-bold mb-4">Ready to find more leads?</h2>
            <p className="text-ice/80 mb-8 leading-relaxed">
              Start a new search to instantly scrape Google Maps, analyze websites, and identify your hottest prospects in minutes.
            </p>
            <div className="flex items-center gap-4">
              <Link
                href="/dashboard/search"
                className="inline-flex items-center justify-center px-6 py-3 rounded-xl bg-gradient-to-r from-steel to-ocean text-offwhite font-semibold hover:from-steel/90 hover:to-ocean/90 hover:scale-105 active:scale-95 transition-all shadow-lg shadow-steel/30"
              >
                <Rocket className="w-5 h-5 mr-2" />
                Start a Search
              </Link>
            </div>
          </div>

          <div className="hidden sm:block absolute top-0 right-0 bottom-0 w-1/2 opacity-10 pointer-events-none">
            <svg viewBox="0 0 400 400" className="absolute right-0 top-1/2 -translate-y-1/2 w-[500px] h-[500px]">
              <path fill="currentColor" d="M48.1,-75.7C62.1,-67.2,72.9,-51.9,80.7,-35C88.4,-18.1,93.2,0.4,89.5,17.4C85.8,34.4,73.6,50,59,61C44.4,72,27.5,78.3,10.1,81.1C-7.4,83.9,-25.3,83.2,-41.2,75.3C-57.1,67.4,-70.9,52.3,-79.8,34.6C-88.7,16.9,-92.7,-3.4,-87.3,-21.2C-81.9,-39.1,-67.1,-54.5,-50.7,-62.4C-34.3,-70.3,-17.1,-70.7,0.7,-71.8C18.5,-72.9,34.1,-84.2,48.1,-75.7Z" transform="translate(200 200) scale(1.1)" />
            </svg>
          </div>
        </GlassCard>

        <div className="space-y-6">
          <GlassCard className="p-6 bg-gradient-to-br from-ocean/30 to-navy border-ocean/40">
            <div className="flex items-center gap-4 mb-4">
              <div className="p-3 rounded-xl bg-emerald-500/10 text-emerald-400">
                <Target className="w-6 h-6" />
              </div>
              <div>
                <h3 className="font-semibold text-offwhite">High Quality Leads</h3>
                <p className="text-sm text-ice/60">Focus on the hot targets</p>
              </div>
            </div>
            <Link
              href="/dashboard/leads?category=hot"
              className="mt-4 block w-full text-center py-2.5 rounded-xl border border-steel/30 text-ice font-medium hover:bg-steel/10 hover:text-offwhite transition-colors"
            >
              View Hot Leads
            </Link>
          </GlassCard>

          <GlassCard className="p-6 bg-gradient-to-br from-ocean/30 to-navy border-ocean/40">
            <div className="flex items-center gap-4 mb-4">
              <div className="p-3 rounded-xl bg-amber-500/10 text-amber-500">
                <Users className="w-6 h-6" />
              </div>
              <div>
                <h3 className="font-semibold text-offwhite">Review Pipeline</h3>
                <p className="text-sm text-ice/60">Manage your new contacts</p>
              </div>
            </div>
            <Link
              href="/dashboard/leads?status=new"
              className="mt-4 block w-full text-center py-2.5 rounded-xl border border-steel/30 text-ice font-medium hover:bg-steel/10 hover:text-offwhite transition-colors"
            >
              View Pipeline
            </Link>
          </GlassCard>
        </div>
      </div>
    </div>
  );
}
