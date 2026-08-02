import type { SupabaseClient, User } from '@supabase/supabase-js';

import { ensureProfileForUser } from '@/lib/ensure-profile';
import { supabase } from '@/lib/supabase';

export class AuthError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'AuthError';
  }
}

/** Returns the authenticated Supabase user from the browser client. */
export async function getCurrentUser(): Promise<User | null> {
  const {
    data: { user },
  } = await supabase.auth.getUser();
  return user;
}

/** Returns the authenticated user id or throws if not signed in. */
export async function requireUserId(): Promise<string> {
  const user = await getCurrentUser();
  if (!user) {
    throw new AuthError('Not authenticated');
  }

  await ensureProfileForUser(supabase, user);
  return user.id;
}

/** Server-side: returns authenticated user from a Supabase server client. */
export async function getServerUser(supabaseClient: SupabaseClient): Promise<User | null> {
  const {
    data: { user },
  } = await supabaseClient.auth.getUser();
  return user;
}

/** Server-side: returns user id or throws. */
export async function requireServerUserId(supabaseClient: SupabaseClient): Promise<string> {
  const user = await getServerUser(supabaseClient);
  if (!user) {
    throw new AuthError('Not authenticated');
  }
  return user.id;
}
