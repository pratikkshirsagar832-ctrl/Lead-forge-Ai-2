'use client';

export const dynamic = 'force-dynamic';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { supabase } from '@/lib/supabase';
import { Loader2 } from 'lucide-react';

export default function AuthCallbackPage() {
  const router = useRouter();
  const [error, setError] = useState('');

  useEffect(() => {
    let mounted = true;

    const handleCallback = async () => {
      try {
        const hashParams = new URLSearchParams(window.location.hash.replace('#', '?'));
        const queryParams = new URLSearchParams(window.location.search);

        // PKCE flow: exchange code for session
        const code = queryParams.get('code');
        if (code) {
          await supabase.auth.exchangeCodeForSession(code);
          if (mounted) router.replace('/dashboard');
          return;
        }

        // Implicit flow: set session from URL hash
        const accessToken = hashParams.get('access_token');
        const refreshToken = hashParams.get('refresh_token');
        if (accessToken && refreshToken) {
          const { error } = await supabase.auth.setSession({
            access_token: accessToken,
            refresh_token: refreshToken,
          } as { access_token: string; refresh_token: string });
          if (!error && mounted) router.replace('/dashboard');
          else throw error || new Error('No session returned');
          return;
        }

        // Already have a session from localStorage
        const { data: { session } } = await supabase.auth.getSession();
        if (mounted && session) {
          router.replace('/dashboard');
          return;
        }

        // Nothing worked — timeout then redirect to login
        setTimeout(() => {
          if (mounted) router.replace('/login');
        }, 3000);
      } catch (err) {
        console.error('Auth callback error:', err);
        if (mounted) setTimeout(() => router.replace('/login'), 3000);
      }
    };

    handleCallback();
  }, [router]);

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-navy font-sans">
        <div className="text-center">
           <p className="text-rose-400 mb-4">{String(error)}</p>
          <button
            onClick={() => router.push('/login')}
            className="px-6 py-2 rounded-lg bg-steel text-offwhite font-semibold hover:opacity-90 transition-opacity"
          >
            Back to Login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-navy font-sans">
      <div className="flex items-center gap-3">
        <Loader2 className="w-6 h-6 text-steel animate-spin" />
        <p className="text-ice/60">Completing sign in...</p>
      </div>
    </div>
  );
}
