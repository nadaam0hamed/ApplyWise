'use client';

import { useCallback, useEffect, useState } from 'react';

import { useApplicationContext } from '@/contexts/ApplicationContext';
import { ApplicationService } from '@/services/application.service';
import type { Application, ApplicationUpdate } from '@/types/application';

type CreateApplicationPayload = Parameters<
  ReturnType<typeof useApplicationContext>['createApplication']
>[0];

export function useApplication(applicationId?: string) {
  const context = useApplicationContext();
  const [application, setApplication] = useState<Application | null>(null);
  const [isLoadingSingle, setIsLoadingSingle] = useState(false);
  const [singleError, setSingleError] = useState<string | null>(null);

  const resolvedId = applicationId ?? context.selectedApplication?.id;

  useEffect(() => {
    if (!applicationId) {
      setApplication(context.selectedApplication);
      setSingleError(null);
      setIsLoadingSingle(false);
      return;
    }

    const fromList = context.applications.find((app) => app.id === applicationId);
    if (fromList) {
      setApplication(fromList);
      setSingleError(null);
      setIsLoadingSingle(false);
      return;
    }

    let mounted = true;
    setIsLoadingSingle(true);
    setSingleError(null);

    ApplicationService.getById(applicationId)
      .then((data) => {
        if (mounted) {
          setApplication(data);
          setIsLoadingSingle(false);
        }
      })
      .catch((err) => {
        if (mounted) {
          setSingleError(err instanceof Error ? err.message : 'Failed to load application');
          setApplication(null);
          setIsLoadingSingle(false);
        }
      });

    return () => {
      mounted = false;
    };
  }, [applicationId, context.selectedApplication, context.applications]);

  const createApplication = useCallback(
    async (payload: CreateApplicationPayload) => {
      const created = await context.createApplication(payload);
      if (!applicationId) {
        setApplication(created);
      }
      return created;
    },
    [context, applicationId],
  );

  const updateApplication = useCallback(
    async (updates: ApplicationUpdate) => {
      if (!resolvedId) {
        throw new Error('No application selected');
      }
      const updated = await context.updateApplication(resolvedId, updates);
      if (applicationId || context.selectedApplication?.id === resolvedId) {
        setApplication(updated);
      }
      return updated;
    },
    [context, resolvedId, applicationId],
  );

  const deleteApplication = useCallback(async () => {
    if (!resolvedId) {
      throw new Error('No application selected');
    }
    await context.deleteApplication(resolvedId);
    setApplication(null);
  }, [context, resolvedId]);

  return {
    application,
    applications: context.applications,
    selectedApplication: context.selectedApplication,
    isLoading: context.isLoading || isLoadingSingle,
    error: context.error ?? singleError,
    selectApplication: context.selectApplication,
    createApplication,
    updateApplication,
    deleteApplication,
    refresh: context.refresh,
  };
}
