/**
 * Shared Supabase environment configuration.
 * Used by both browser and server clients.
 */
export function getSupabaseEnv(): { url: string; anonKey: string } {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  // Allow missing env vars during build time for static pages
  if (process.env.NODE_ENV === 'production' && !url && !anonKey) {
    throw new Error(
      'Missing Supabase environment variables. Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY.',
    );
  }

  return { url: url || '', anonKey: anonKey || '' };
}

export function getSupabaseServiceEnv(): { url: string; serviceKey: string } {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

  // Allow missing env vars during build time for static pages
  if (process.env.NODE_ENV === 'production' && !url && !serviceKey) {
    throw new Error(
      'Missing Supabase service role environment variables. Set NEXT_PUBLIC_SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.',
    );
  }

  return { url: url || '', serviceKey: serviceKey || '' };
}
