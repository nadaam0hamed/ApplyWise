/**
 * Shared Supabase environment configuration.
 * Used by both browser and server clients.
 */
export function getSupabaseEnv(): { url: string; anonKey: string } {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  // Allow missing env vars during build time for static pages
  if (!url || !anonKey) {
    // Return empty strings during build time
    return { url: url || '', anonKey: anonKey || '' };
  }

  return { url, anonKey };
}

export function getSupabaseServiceEnv(): { url: string; serviceKey: string } {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

  // Allow missing env vars during build time for static pages
  if (!url || !serviceKey) {
    // Return empty strings during build time
    return { url: url || '', serviceKey: serviceKey || '' };
  }

  return { url, serviceKey };
}
