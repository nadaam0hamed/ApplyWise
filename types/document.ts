import type { DocumentType } from '@/constants/documentTypes';

/**
 * Maps to the `documents` Supabase table.
 * Columns: id, application_id, file_name, document_type, storage_path,
 * uploaded_at, file_size, mime_type
 */
export interface Document {
  id: string;
  application_id: string;
  file_name: string;
  document_type: DocumentType | null;
  storage_path: string;
  uploaded_at: string;
  file_size: number;
  mime_type: string;
}

/** Payload for inserting a document record after upload. */
export interface DocumentInsert {
  application_id: string;
  file_name: string;
  document_type: DocumentType;
  storage_path: string;
  file_size: number;
  mime_type: string;
  uploaded_at?: string;
}

/** Payload for updating a document row. */
export type DocumentUpdate = Partial<
  Omit<Document, 'id' | 'application_id' | 'uploaded_at'>
>;

/** Summary shape used in analysis and dashboard lists. */
export interface DocumentSummary {
  id: string;
  file_name: string;
  document_type: DocumentType | null;
  uploaded_at: string;
}
