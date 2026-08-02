import { RAG_SOURCE_COLUMNS } from '@/lib/supabase-live-schema';
import { createServerSupabaseClient } from '@/lib/serverSupabase';

/** Maps to the live `rag_sources` Supabase table. */
export type RagSource = {
  id: string;
  application_id: string;
  source_url: string;
  created_at: string;
};

// TODO: Vector search and RAG document chunks using `rag_sources` ({RAG_SOURCE_COLUMNS})
// TODO: In each method: const supabase = await createServerSupabaseClient()

export const RagService = {};
