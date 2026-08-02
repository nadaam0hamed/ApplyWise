import { DOCUMENTS_BUCKET } from '@/lib/storage';
import { getSupabaseEnv } from '@/lib/supabase-env';
import { supabase } from '@/lib/supabase';

/** Uploads a file to the documents bucket at the given storage path. */
export async function uploadDocumentToStorage(
  storagePath: string,
  file: File,
  onProgress?: (percent: number) => void,
): Promise<void> {
  if (onProgress) {
    await uploadToStorageWithProgress(storagePath, file, onProgress);
    return;
  }

  const { error } = await supabase.storage.from(DOCUMENTS_BUCKET).upload(storagePath, file, {
    upsert: true,
    contentType: file.type || 'application/octet-stream',
  });

  if (error) {
    throw new Error(error.message);
  }
}

/** Uploads via the Storage REST API so XMLHttpRequest can report upload progress. */
async function uploadToStorageWithProgress(
  storagePath: string,
  file: File,
  onProgress?: (percent: number) => void,
): Promise<void> {
  const { url, anonKey } = getSupabaseEnv();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (!session?.access_token) {
    throw new Error('Not authenticated');
  }

  const encodedPath = storagePath
    .split('/')
    .map((segment) => encodeURIComponent(segment))
    .join('/');
  const uploadUrl = `${url}/storage/v1/object/${DOCUMENTS_BUCKET}/${encodedPath}`;

  await new Promise<void>((resolve, reject) => {
    const xhr = new XMLHttpRequest();

    xhr.upload.addEventListener('progress', (event) => {
      if (event.lengthComputable && onProgress) {
        onProgress(Math.round((event.loaded / event.total) * 100));
      }
    });

    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        onProgress?.(100);
        resolve();
        return;
      }

      try {
        const body = JSON.parse(xhr.responseText) as { message?: string; error?: string };
        reject(new Error(body.message ?? body.error ?? `Upload failed (${xhr.status})`));
      } catch {
        reject(new Error(`Upload failed (${xhr.status})`));
      }
    });

    xhr.addEventListener('error', () => reject(new Error('Upload failed')));
    xhr.open('POST', uploadUrl);
    xhr.setRequestHeader('Authorization', `Bearer ${session.access_token}`);
    xhr.setRequestHeader('apikey', anonKey);
    xhr.setRequestHeader('Content-Type', file.type || 'application/octet-stream');
    xhr.setRequestHeader('x-upsert', 'true');
    xhr.send(file);
  });
}
