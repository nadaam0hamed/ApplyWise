import { supabase } from '@/lib/supabase';

/** Supabase Storage bucket for user document uploads. */
export const DOCUMENTS_BUCKET = 'documents';

/** Default expiry for signed download/preview URLs (seconds). */
export const DOCUMENT_SIGNED_URL_TTL = 3600;

/** Builds a user-scoped storage path: {userId}/{applicationId}/{fileName}. */
export function buildDocumentStoragePath(
  userId: string,
  applicationId: string,
  fileName: string,
): string {
  return `${userId}/${applicationId}/${fileName}`;
}

/** Creates a signed URL for an object in the documents bucket. */
export async function createDocumentSignedUrl(storagePath: string): Promise<string> {
  const { data, error } = await supabase.storage
    .from(DOCUMENTS_BUCKET)
    .createSignedUrl(storagePath, DOCUMENT_SIGNED_URL_TTL);

  if (error) {
    throw new Error(error.message);
  }
  if (!data?.signedUrl) {
    throw new Error('Failed to generate signed URL');
  }

  return data.signedUrl;
}

/** Removes one or more objects from the documents bucket. */
export async function removeDocumentsFromStorage(storagePaths: string[]): Promise<void> {
  if (storagePaths.length === 0) {
    return;
  }

  const { error } = await supabase.storage.from(DOCUMENTS_BUCKET).remove(storagePaths);
  if (error) {
    throw new Error(error.message);
  }
}
