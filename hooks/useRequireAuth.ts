'use client';

import { useAuth } from '@/hooks/useAuth';

export function useRequireAuth() {
  const { user, loading } = useAuth();

  return { user, loading };
}
