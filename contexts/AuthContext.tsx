'use client';

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import { useRouter } from 'next/navigation';

import { AuthService } from '@/services/auth.service';
import type { AuthUser } from '@/types/auth';

type AuthContextValue = {
  user: AuthUser | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<{ error: string | null; hasSession: boolean }>;
  signup: (
    fullName: string,
    email: string,
    password: string,
  ) => Promise<{ error: string | null; hasSession: boolean }>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;

    AuthService.getSessionUser()
      .then((sessionUser) => {
        if (mounted) {
          setUser(sessionUser);
          setLoading(false);
        }
      })
      .catch(() => {
        if (mounted) {
          setUser(null);
          setLoading(false);
        }
      });

    const unsubscribe = AuthService.subscribeToAuthChanges((nextUser) => {
      if (mounted) {
        setUser(nextUser);
        setLoading(false);
      }
    });

    return () => {
      mounted = false;
      unsubscribe();
    };
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const result = await AuthService.signIn(email, password);

    if (result.error) {
      return { error: result.error, hasSession: false };
    }

    const sessionUser = await AuthService.getSessionUser();
    setUser(sessionUser);

    return { error: null, hasSession: Boolean(sessionUser) };
  }, []);

  const signup = useCallback(
    async (fullName: string, email: string, password: string) => {
      const result = await AuthService.signUp(fullName, email, password);

      if (result.error) {
        return { error: result.error, hasSession: false };
      }

      const sessionUser = await AuthService.getSessionUser();
      setUser(sessionUser);

      return { error: null, hasSession: Boolean(sessionUser) };
    },
    [],
  );

  const logout = useCallback(async () => {
    await AuthService.signOut();
    setUser(null);
    router.push('/login');
  }, [router]);

  const value = useMemo(
    () => ({
      user,
      loading,
      login,
      signup,
      logout,
    }),
    [user, loading, login, signup, logout],
  );

  return (
    <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
  );
}

export function useAuthContext(): AuthContextValue {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error('useAuthContext must be used within an AuthProvider');
  }

  return context;
}
