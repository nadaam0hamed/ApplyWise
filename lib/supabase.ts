'use client';

import { createBrowserClient } from '@supabase/ssr';
import type { SupabaseClient } from '@supabase/supabase-js';

import { getSupabaseEnv } from '@/lib/supabase-env';

let browserClient: SupabaseClient | undefined;

/**
 * Creates a Supabase client for use in Client Components, hooks, and browser code.
 * Prefer this factory when you need an isolated instance (e.g. tests).
 */
export function createClient(): SupabaseClient {
  const { url, anonKey } = getSupabaseEnv();
  return createBrowserClient(url, anonKey);
}

/**
 * Returns a singleton browser Supabase client.
 * Reuses the same instance across Client Component renders.
 */
export function getSupabaseClient(): SupabaseClient {
  if (!browserClient) {
    browserClient = createClient();
  }
  return browserClient;
}

/** Shared browser Supabase client — import this in hooks and Client Components. */
export const supabase = getSupabaseClient();
