"""Live Supabase column lists (mirrors frontend supabase-live-schema.ts)."""

APPLICATION_COLUMNS = (
    "id,user_id,application_type,status,title,country,source_url,readiness_score,created_at"
)
DOCUMENT_COLUMNS = (
    "id,application_id,file_name,document_type,storage_path,uploaded_at,file_size,mime_type"
)
REQUIREMENT_COLUMNS = "id,application_id,category,created_at"
REQUIREMENT_STATUS_COLUMNS = "id,requirement_id,status,created_at"
AI_ANALYSIS_COLUMNS = (
    "id,application_id,readiness_score,missing_documents,recommendations,strengths,weaknesses,created_at"
)
