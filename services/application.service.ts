import { requireUserId } from '@/lib/auth-helpers';
import {
  AI_ANALYSIS_COLUMNS,
  APPLICATION_COLUMNS,
  DOCUMENT_COLUMNS,
  REQUIREMENT_COLUMNS,
  TIMELINE_TASK_COLUMNS,
} from '@/lib/supabase-live-schema';
import { supabase } from '@/lib/supabase';
import type {
  Application,
  ApplicationInsert,
  ApplicationUpdate,
  ApplicationWithRelations,
} from '@/types/application';
import { ApplicationStatus } from '@/constants/applicationStatus';

function toApplicationRow(
  payload: Omit<ApplicationInsert, 'user_id'> | ApplicationUpdate,
): Record<string, unknown> {
  const row: Record<string, unknown> = {};

  if ('application_type' in payload && payload.application_type !== undefined) {
    row.application_type = payload.application_type;
  }
  if ('status' in payload && payload.status !== undefined) {
    row.status = payload.status;
  }
  if ('title' in payload && payload.title !== undefined) {
    row.title = payload.title;
  }
  if ('country' in payload && payload.country !== undefined) {
    row.country = payload.country;
  }
  if ('source_url' in payload && payload.source_url !== undefined) {
    row.source_url = payload.source_url;
  }
  if ('readiness_score' in payload && payload.readiness_score !== undefined) {
    row.readiness_score = payload.readiness_score;
  }

  return row;
}

export const ApplicationService = {
  /** Returns all applications for the authenticated user, newest first. */
  async listForUser(): Promise<Application[]> {
    const userId = await requireUserId();

    const { data, error } = await supabase
      .from('applications')
      .select(APPLICATION_COLUMNS)
      .eq('user_id', userId)
      .order('created_at', { ascending: false });

    if (error) throw new Error(error.message);
    return (data ?? []) as Application[];
  },

  /** Returns the most recent application for the authenticated user. */
  async getLatestForUser(): Promise<Application | null> {
    const userId = await requireUserId();

    const { data, error } = await supabase
      .from('applications')
      .select(APPLICATION_COLUMNS)
      .eq('user_id', userId)
      .order('created_at', { ascending: false })
      .limit(1)
      .maybeSingle();

    if (error) throw new Error(error.message);
    return data as Application | null;
  },

  /** Returns a single application owned by the authenticated user. */
  async getById(applicationId: string): Promise<Application | null> {
    const userId = await requireUserId();

    const { data, error } = await supabase
      .from('applications')
      .select(APPLICATION_COLUMNS)
      .eq('id', applicationId)
      .eq('user_id', userId)
      .maybeSingle();

    if (error) throw new Error(error.message);
    return data as Application | null;
  },

  /** Returns an application with related requirements, documents, and timeline events. */
  async getWithRelations(applicationId: string): Promise<ApplicationWithRelations | null> {
    const userId = await requireUserId();

    const { data: application, error: appError } = await supabase
      .from('applications')
      .select(APPLICATION_COLUMNS)
      .eq('id', applicationId)
      .eq('user_id', userId)
      .maybeSingle();

    if (appError) throw new Error(appError.message);
    if (!application) return null;

    const [requirementsResult, documentsResult, timelineResult, analysisResult] =
      await Promise.all([
        supabase
          .from('requirements')
          .select(REQUIREMENT_COLUMNS)
          .eq('application_id', applicationId)
          .order('created_at', { ascending: true }),
        supabase
          .from('documents')
          .select(DOCUMENT_COLUMNS)
          .eq('application_id', applicationId)
          .order('uploaded_at', { ascending: false }),
        supabase
          .from('timeline_tasks')
          .select(TIMELINE_TASK_COLUMNS)
          .eq('application_id', applicationId)
          .order('created_at', { ascending: true }),
        supabase
          .from('ai_analysis')
          .select(AI_ANALYSIS_COLUMNS)
          .eq('application_id', applicationId)
          .order('created_at', { ascending: false })
          .limit(1)
          .maybeSingle(),
      ]);

    if (requirementsResult.error) throw new Error(requirementsResult.error.message);
    if (documentsResult.error) throw new Error(documentsResult.error.message);
    if (timelineResult.error) throw new Error(timelineResult.error.message);
    if (analysisResult.error) throw new Error(analysisResult.error.message);

    return {
      ...(application as Application),
      requirements: requirementsResult.data ?? [],
      documents: documentsResult.data ?? [],
      timeline_tasks: timelineResult.data ?? [],
      analysis: analysisResult.data ?? null,
    };
  },

  /** Creates a new application with user_id set from auth. */
  async create(payload: Omit<ApplicationInsert, 'user_id'>): Promise<Application> {
    const userId = await requireUserId();

    const { data, error } = await supabase
      .from('applications')
      .insert({
        ...toApplicationRow(payload),
        user_id: userId,
        status: payload.status ?? ApplicationStatus.InProgress,
      })
      .select(APPLICATION_COLUMNS)
      .single();

    if (error) throw new Error(error.message);
    return data as Application;
  },

  /** Updates an application owned by the authenticated user. */
  async update(applicationId: string, updates: ApplicationUpdate): Promise<Application> {
    const userId = await requireUserId();

    const { data, error } = await supabase
      .from('applications')
      .update(toApplicationRow(updates))
      .eq('id', applicationId)
      .eq('user_id', userId)
      .select(APPLICATION_COLUMNS)
      .single();

    if (error) throw new Error(error.message);
    return data as Application;
  },

  /** Deletes an application owned by the authenticated user. */
  async delete(applicationId: string): Promise<void> {
    const userId = await requireUserId();

    const { error } = await supabase
      .from('applications')
      .delete()
      .eq('id', applicationId)
      .eq('user_id', userId);

    if (error) throw new Error(error.message);
  },
};
