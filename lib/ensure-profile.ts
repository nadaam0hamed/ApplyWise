import type { SupabaseClient, User } from '@supabase/supabase-js';

import { PROFILE_COLUMNS } from '@/lib/supabase-live-schema';

export type ProfileSummary = {
  full_name: string | null;
  email: string;
};

function fullNameFromUser(user: User, fullNameHint?: string | null): string | null {
  if (fullNameHint?.trim()) {
    return fullNameHint.trim();
  }

  const metadataName = user.user_metadata?.full_name;
  if (typeof metadataName === 'string' && metadataName.trim()) {
    return metadataName.trim();
  }

  return null;
}

function buildProfileRow(user: User, fullNameHint?: string | null) {
  const email = user.email?.trim() ?? '';

  return {
    id: user.id,
    full_name: fullNameFromUser(user, fullNameHint),
    email,
  };
}

/**
 * Ensures public.profiles has a row for the authenticated user.
 * Idempotent: no-op when a profile already exists; safe under concurrent inserts.
 */
export async function ensureProfileForUser(
  supabase: SupabaseClient,
  user: User,
  fullNameHint?: string | null,
): Promise<ProfileSummary> {
  const { data: existing, error: fetchError } = await supabase
    .from('profiles')
    .select(PROFILE_COLUMNS)
    .eq('id', user.id)
    .maybeSingle();

  if (fetchError) {
    throw new Error(fetchError.message);
  }

  if (existing) {
    return existing;
  }

  const row = buildProfileRow(user, fullNameHint);

  if (!row.email) {
    throw new Error('Cannot create profile: authenticated user has no email.');
  }

  const { error: insertError } = await supabase.from('profiles').insert({
    id: row.id,
    full_name: row.full_name,
    email: row.email,
  });

  if (insertError) {
    if (insertError.code === '23505') {
      const { data: raced, error: raceFetchError } = await supabase
        .from('profiles')
        .select(PROFILE_COLUMNS)
        .eq('id', user.id)
        .maybeSingle();

      if (raceFetchError) {
        throw new Error(raceFetchError.message);
      }

      if (raced) {
        return raced;
      }
    }

    throw new Error(insertError.message);
  }

  return { full_name: row.full_name, email: row.email };
}
