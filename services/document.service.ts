import { requireUserId } from '@/lib/auth-helpers';
import { DOCUMENT_COLUMNS } from '@/lib/supabase-live-schema';
import { supabase } from '@/lib/supabase';
import {
  buildDocumentStoragePath,
  createDocumentSignedUrl,
  removeDocumentsFromStorage,
} from '@/lib/storage';
import { uploadDocumentToStorage } from '@/lib/storage-upload';
import { SUPPORTED_MIME_TYPES, type DocumentType } from '@/constants/documentTypes';
import { ApplicationService } from '@/services/application.service';
import type { Document, DocumentInsert } from '@/types/document';

function sanitizeFileName(fileName: string): string {
  return fileName.replace(/[^a-zA-Z0-9._-]/g, '_');
}

function buildStoragePath(userId: string, applicationId: string, fileName: string): string {
  return buildDocumentStoragePath(userId, applicationId, sanitizeFileName(fileName));
}

async function assertOwnApplication(applicationId: string): Promise<void> {
  const application = await ApplicationService.getById(applicationId);
  if (!application) {
    throw new Error('Application not found');
  }
}

export const DocumentService = {
  async listByApplication(applicationId: string): Promise<Document[]> {
    await assertOwnApplication(applicationId);

    const { data, error } = await supabase
      .from('documents')
      .select(DOCUMENT_COLUMNS)
      .eq('application_id', applicationId)
      .order('uploaded_at', { ascending: false });

    if (error) throw new Error(error.message);
    return (data ?? []) as Document[];
  },

  async findForTypes(
    applicationId: string,
    documentTypes: DocumentType[],
  ): Promise<Document | null> {
    await assertOwnApplication(applicationId);

    const { data, error } = await supabase
      .from('documents')
      .select(DOCUMENT_COLUMNS)
      .eq('application_id', applicationId)
      .in('document_type', documentTypes)
      .order('uploaded_at', { ascending: false })
      .limit(1)
      .maybeSingle();

    if (error) throw new Error(error.message);
    return (data as Document | null) ?? null;
  },

  async upload(
    applicationId: string,
    file: File,
    documentType: DocumentType,
    onProgress?: (percent: number) => void,
    clearTypes?: DocumentType[],
  ): Promise<Document> {
    const userId = await requireUserId();
    await assertOwnApplication(applicationId);

    if (!SUPPORTED_MIME_TYPES.includes(file.type as (typeof SUPPORTED_MIME_TYPES)[number])) {
      throw new Error(`Unsupported file type: ${file.type || 'unknown'}`);
    }

    const typesToClear = clearTypes ?? [documentType];
    const { data: existingDocs, error: existingError } = await supabase
      .from('documents')
      .select('id')
      .eq('application_id', applicationId)
      .in('document_type', typesToClear);

    if (existingError) throw new Error(existingError.message);

    for (const existing of existingDocs ?? []) {
      await DocumentService.delete(existing.id, applicationId);
    }

    const storagePath = buildStoragePath(userId, applicationId, file.name);

    await uploadDocumentToStorage(storagePath, file, onProgress);

    const now = new Date().toISOString();
    const payload: DocumentInsert = {
      application_id: applicationId,
      file_name: file.name,
      mime_type: file.type,
      file_size: file.size,
      storage_path: storagePath,
      document_type: documentType,
      uploaded_at: now,
    };

    const { data, error } = await supabase
      .from('documents')
      .insert(payload)
      .select(DOCUMENT_COLUMNS)
      .single();

    if (error) {
      await removeDocumentsFromStorage([storagePath]).catch(() => undefined);
      throw new Error(error.message);
    }

    return data as Document;
  },

  async replace(
    applicationId: string,
    file: File,
    documentType: DocumentType,
    onProgress?: (percent: number) => void,
    clearTypes?: DocumentType[],
  ): Promise<Document> {
    return DocumentService.upload(
      applicationId,
      file,
      documentType,
      onProgress,
      clearTypes,
    );
  },

  async getPreviewUrl(documentId: string, applicationId: string): Promise<string> {
    await assertOwnApplication(applicationId);

    const { data: doc, error: fetchError } = await supabase
      .from('documents')
      .select('storage_path')
      .eq('id', documentId)
      .eq('application_id', applicationId)
      .single();

    if (fetchError) throw new Error(fetchError.message);

    return createDocumentSignedUrl(doc.storage_path);
  },

  async delete(documentId: string, applicationId: string): Promise<void> {
    await assertOwnApplication(applicationId);

    const { data: doc, error: fetchError } = await supabase
      .from('documents')
      .select('storage_path')
      .eq('id', documentId)
      .eq('application_id', applicationId)
      .single();

    if (fetchError) throw new Error(fetchError.message);

    await removeDocumentsFromStorage([doc.storage_path]);

    const { error } = await supabase
      .from('documents')
      .delete()
      .eq('id', documentId)
      .eq('application_id', applicationId);

    if (error) throw new Error(error.message);
  },
};
