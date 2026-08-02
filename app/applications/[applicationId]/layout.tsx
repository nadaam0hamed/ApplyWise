'use client';

import { AuthGuard } from '@/components/auth/AuthGuard';
import { ApplicationProvider } from '@/contexts/ApplicationContext';

export default function ApplicationLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard>
      <ApplicationProvider>{children}</ApplicationProvider>
    </AuthGuard>
  );
}
