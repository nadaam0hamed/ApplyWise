import type { ApplicationStatus, ApplicationType } from '@/constants/applicationStatus';

/**
 * Maps to the live `applications` Supabase table.
 * Columns: id, user_id, application_type, status, title, country,
 * source_url, readiness_score, created_at
 */
export interface Application {
  id: string;
  user_id: string;
  application_type: ApplicationType;
  status: ApplicationStatus;
  title: string | null;
  country: string | null;
  source_url: string | null;
  readiness_score: number | null;
  created_at: string;
}

/** Payload for creating a new application record. */
export interface ApplicationInsert {
  user_id: string;
  application_type: ApplicationType;
  status?: ApplicationStatus;
  title?: string | null;
  country?: string | null;
  source_url?: string | null;
  readiness_score?: number | null;
}

/** Payload for updating an existing application. */
export type ApplicationUpdate = Partial<
  Omit<Application, 'id' | 'user_id' | 'created_at'>
>;

/** Application with related entities for dashboard views. */
export interface ApplicationWithRelations extends Application {
  documents?: import('@/types/document').Document[];
  requirements?: import('@/types/requirement').Requirement[];
  analysis?: import('@/types/analysis').Analysis | null;
  timeline_tasks?: import('@/types/timeline').TimelineTask[];
}
