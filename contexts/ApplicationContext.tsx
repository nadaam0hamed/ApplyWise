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

import { useAuth } from '@/hooks/useAuth';
import { ApplicationService } from '@/services/application.service';
import type { Application, ApplicationInsert, ApplicationUpdate } from '@/types/application';

const SELECTED_APPLICATION_KEY = 'applywise:selectedApplicationId';

type CreateApplicationPayload = Omit<ApplicationInsert, 'user_id'>;

type ApplicationContextValue = {
  applications: Application[];
  selectedApplication: Application | null;
  isLoading: boolean;
  error: string | null;
  selectApplication: (applicationId: string | null) => void;
  createApplication: (payload: CreateApplicationPayload) => Promise<Application>;
  updateApplication: (
    applicationId: string,
    updates: ApplicationUpdate,
  ) => Promise<Application>;
  deleteApplication: (applicationId: string) => Promise<void>;
  refresh: () => Promise<void>;
};

const ApplicationContext = createContext<ApplicationContextValue | undefined>(undefined);

export function ApplicationProvider({ children }: { children: ReactNode }) {
  const { user, loading: authLoading } = useAuth();
  const [applications, setApplications] = useState<Application[]>([]);
  const [selectedApplicationId, setSelectedApplicationId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const selectApplication = useCallback((applicationId: string | null) => {
    setSelectedApplicationId(applicationId);
    if (applicationId) {
      sessionStorage.setItem(SELECTED_APPLICATION_KEY, applicationId);
    } else {
      sessionStorage.removeItem(SELECTED_APPLICATION_KEY);
    }
  }, []);

  const refresh = useCallback(async () => {
    if (!user) {
      setApplications([]);
      setSelectedApplicationId(null);
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const list = await ApplicationService.listForUser();
      setApplications(list);

      const storedId = sessionStorage.getItem(SELECTED_APPLICATION_KEY);
      const validStored = storedId && list.some((app) => app.id === storedId);
      const nextSelectedId = validStored ? storedId : list[0]?.id ?? null;

      setSelectedApplicationId(nextSelectedId);
      if (nextSelectedId) {
        sessionStorage.setItem(SELECTED_APPLICATION_KEY, nextSelectedId);
      } else {
        sessionStorage.removeItem(SELECTED_APPLICATION_KEY);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load applications');
      setApplications([]);
    } finally {
      setIsLoading(false);
    }
  }, [user]);

  useEffect(() => {
    if (authLoading) return;

    if (!user) {
      setApplications([]);
      setSelectedApplicationId(null);
      setIsLoading(false);
      return;
    }

    refresh();
  }, [user, authLoading, refresh]);

  const createApplication = useCallback(
    async (payload: CreateApplicationPayload) => {
      setError(null);
      const created = await ApplicationService.create(payload);
      await refresh();
      selectApplication(created.id);
      return created;
    },
    [refresh, selectApplication],
  );

  const updateApplication = useCallback(
    async (applicationId: string, updates: ApplicationUpdate) => {
      setError(null);
      const updated = await ApplicationService.update(applicationId, updates);
      setApplications((prev) =>
        prev.map((app) => (app.id === applicationId ? updated : app)),
      );
      return updated;
    },
    [],
  );

  const deleteApplication = useCallback(
    async (applicationId: string) => {
      setError(null);
      await ApplicationService.delete(applicationId);

      setApplications((prev) => {
        const remaining = prev.filter((app) => app.id !== applicationId);

        if (selectedApplicationId === applicationId) {
          const nextId = remaining[0]?.id ?? null;
          selectApplication(nextId);
        }

        return remaining;
      });
    },
    [selectedApplicationId, selectApplication],
  );

  const selectedApplication = useMemo(
    () => applications.find((app) => app.id === selectedApplicationId) ?? null,
    [applications, selectedApplicationId],
  );

  const value = useMemo(
    () => ({
      applications,
      selectedApplication,
      isLoading,
      error,
      selectApplication,
      createApplication,
      updateApplication,
      deleteApplication,
      refresh,
    }),
    [
      applications,
      selectedApplication,
      isLoading,
      error,
      selectApplication,
      createApplication,
      updateApplication,
      deleteApplication,
      refresh,
    ],
  );

  return (
    <ApplicationContext.Provider value={value}>{children}</ApplicationContext.Provider>
  );
}

export function useApplicationContext(): ApplicationContextValue {
  const context = useContext(ApplicationContext);

  if (!context) {
    throw new Error('useApplicationContext must be used within an ApplicationProvider');
  }

  return context;
}
