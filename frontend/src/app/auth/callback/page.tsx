'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { supabase } from '@/lib/supabase';
import { Loader2 } from 'lucide-react';

export default function AuthCallbackPage() {
  const router = useRouter();
  const [error, setError] = useState('');

  useEffect(() => {
    let mounted = true;
    let completed = false;

    const redirectToDashboard = () => {
      if (completed) return;
      completed = true;
      router.replace('/dashboard');
    };

    const redirectToLogin = () => {
      if (completed) return;
      completed = true;
      router.replace('/login');
    };

    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (event, session) => {
        if (!mounted) return;
        if (event === 'SIGNED_IN' && session) {
          redirectToDashboard();
        }
      }
    );

    supabase.auth.getSession().then((result) => {
      if (mounted && result.data?.session) {
        redirectToDashboard();
      }
    }).catch((err) => {
      console.error('Auth callback: getSession error', err);
    });

    const timeout = setTimeout(() => {
      if (mounted) redirectToLogin();
    }, 15000);

    return () => {
      mounted = false;
      subscription.unsubscribe();
      clearTimeout(timeout);
    };
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
