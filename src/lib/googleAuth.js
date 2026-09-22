import supabase from './supabase';

export async function signInWithGoogle() {
  const next = new URLSearchParams(window.location.search).get('next') || '/dashboard';
  const { error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo: `${window.location.origin}/auth?next=${encodeURIComponent(next)}`,
      queryParams: { prompt: 'select_account' },
    },
  });
  if (error) {
    console.error('[google-auth]', error.message);
    return { error };
  }
  return { error: null };
}
