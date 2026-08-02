/**
 * Live Supabase column lists (verified via PostgREST).
 * Do not infer schema from supabase/migrations — use these constants for queries.
 */
export const PROFILE_COLUMNS =
  'id,full_name,email,created_at' as const;

export const APPLICATION_COLUMNS =
  'id,user_id,application_type,status,title,country,source_url,readiness_score,created_at' as const;

export const DOCUMENT_COLUMNS =
  'id,application_id,file_name,document_type,storage_path,uploaded_at,file_size,mime_type' as const;

export const REQUIREMENT_COLUMNS =
  'id,application_id,category,created_at' as const;

export const REQUIREMENT_STATUS_COLUMNS =
  'id,requirement_id,status,created_at' as const;

export const TIMELINE_TASK_COLUMNS =
  'id,application_id,completed,created_at,due_date' as const;

export const AI_ANALYSIS_COLUMNS =
  'id,application_id,readiness_score,missing_documents,recommendations,strengths,weaknesses,created_at' as const;

export const CHAT_HISTORY_COLUMNS =
  'id,application_id,role,message,created_at' as const;

export const RAG_SOURCE_COLUMNS =
  'id,application_id,source_url,created_at' as const;
