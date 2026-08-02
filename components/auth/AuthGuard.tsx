'use client';

import type { ReactNode } from 'react';

import { useRequireAuth } from '@/hooks/useRequireAuth';

export function AuthGuard({ children }: { children: ReactNode }) {
  const { user, loading } = useRequireAuth();

  if (loading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        Loading...
      </div>
    );
  }

  return <>{children}</>;
}
