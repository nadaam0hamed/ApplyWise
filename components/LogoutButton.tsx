'use client';

import { LogOut } from 'lucide-react';

import { useAuth } from '@/hooks/useAuth';

type LogoutButtonProps = {
  className?: string;
  showIcon?: boolean;
  label?: string;
};

export function LogoutButton({
  className,
  showIcon = true,
  label = 'Logout',
}: LogoutButtonProps) {
  const { logout } = useAuth();

  return (
    <button
      type="button"
      onClick={() => logout()}
      className={
        className ??
        'px-6 py-2 text-sm font-medium text-foreground border border-primary/30 hover:border-primary rounded-lg transition-colors flex items-center gap-2'
      }
    >
      {showIcon && <LogOut size={16} />}
      {label}
    </button>
  );
}
