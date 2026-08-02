import type { User } from '@supabase/supabase-js';

import { ensureProfileForUser } from '@/lib/ensure-profile';
import { supabase } from '@/lib/supabase';
import type { AuthResult, AuthUser } from '@/types/auth';

function mapUserToAuthUser(user: User, fullName?: string | null): AuthUser {
  return {
    id: user.id,
    email: user.email ?? '',
    fullName: fullName ?? (user.user_metadata?.full_name as string | undefined) ?? null,
  };
}

async function resolveAuthUser(user: User): Promise<AuthUser> {
  const profile = await ensureProfileForUser(supabase, user);
  return mapUserToAuthUser(user, profile.full_name);
}

export const AuthService = {
  async getSessionUser(): Promise<AuthUser | null> {
    const {
      data: { session },
    } = await supabase.auth.getSession();

    if (!session?.user) {
      return null;
    }

    return resolveAuthUser(session.user);
  },

  subscribeToAuthChanges(callback: (user: AuthUser | null) => void): () => void {
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (_event, session) => {
      if (session?.user) {
        callback(await resolveAuthUser(session.user));
        return;
      }

      callback(null);
    });

    return () => subscription.unsubscribe();
  },

  async signIn(email: string, password: string): Promise<AuthResult> {
    const { error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    return { error: error?.message ?? null };
  },

  async signUp(
    fullName: string,
    email: string,
    password: string,
  ): Promise<AuthResult> {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: { full_name: fullName },
      },
    });

    if (error) {
      return { error: error.message };
    }

    if (!data.user) {
      return { error: 'Sign up failed. Please try again.' };
    }

    // Profile insert requires an authenticated session (RLS: auth.uid() = id).
    if (data.session) {
      try {
        await ensureProfileForUser(supabase, data.session.user, fullName);
      } catch (profileError) {
        const message =
          profileError instanceof Error ? profileError.message : 'Failed to create profile.';
        return { error: message };
      }
    }

    return { error: null };
  },

  async signOut(): Promise<void> {
    await supabase.auth.signOut();
  },
};
