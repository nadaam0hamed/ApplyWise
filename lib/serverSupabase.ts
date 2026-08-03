import { createServerClient } from '@supabase/ssr';
import { cookies } from 'next/headers';
import { createClient } from '@supabase/supabase-js';
import type { SupabaseClient } from '@supabase/supabase-js';

import { getSupabaseEnv, getSupabaseServiceEnv } from '@/lib/supabase-env';

/**
 * Creates a Supabase client for Server Components, Route Handlers, and Server Actions.
 * Reads and writes auth session cookies via Next.js `cookies()`.
 *
 * Call once per request — do not cache the returned client across requests.
 */
export async function createServerSupabaseClient(): Promise<SupabaseClient> {
  const { url, anonKey } = getSupabaseEnv();
  const cookieStore = await cookies();

  return createServerClient(url, anonKey, {
    cookies: {
      getAll() {
        return cookieStore.getAll();
      },
      setAll(cookiesToSet) {
        try {
          cookiesToSet.forEach(({ name, value, options }) => {
            cookieStore.set(name, value, options);
          });
        } catch {
          // Called from a Server Component that cannot set cookies — safe to ignore.
        }
      },
    },
  });
}

/**
 * Creates a Supabase client with service role privileges for server-side operations.
 * Bypasses RLS policies — use only for trusted server operations.
 */
export function createServiceSupabaseClient(): SupabaseClient {
  const { url, serviceKey } = getSupabaseServiceEnv();
  return createClient(url, serviceKey, {
    auth: {
      autoRefreshToken: false,
      persistSession: false,
    },
  });
}
