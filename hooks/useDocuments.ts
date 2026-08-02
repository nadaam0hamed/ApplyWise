'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';

import {
  APPLICATION_DOCUMENT_SLOTS,
  type ApplicationDocumentSlot,
  type DocumentType,
} from '@/constants/documentTypes';
import { DocumentService } from '@/services/document.service';
import type { Document } from '@/types/document';

function findDocumentForSlot(
  documents: Document[],
  slot: ApplicationDocumentSlot,
): Document | undefined {
  return documents.find(
    (doc) => doc.document_type && slot.documentTypes.includes(doc.document_type),
  );
}

export function useDocuments(applicationId: string) {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({});
  const [uploadingSlot, setUploadingSlot] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const list = await DocumentService.listByApplication(applicationId);
      setDocuments(list);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load documents');
      setDocuments([]);
    } finally {
      setIsLoading(false);
    }
  }, [applicationId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const uploadDocument = useCallback(
    async (slot: ApplicationDocumentSlot, file: File) => {
      setUploadingSlot(slot.key);
      setUploadProgress((prev) => ({ ...prev, [slot.key]: 0 }));
      setError(null);

      try {
        const doc = await DocumentService.upload(
          applicationId,
          file,
          slot.defaultDocumentType,
          (percent) => setUploadProgress((prev) => ({ ...prev, [slot.key]: percent })),
          slot.documentTypes,
        );
        await refresh();
        return doc;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Upload failed';
        setError(message);
        throw err;
      } finally {
        setUploadingSlot(null);
      }
    },
    [applicationId, refresh],
  );

  const replaceDocument = useCallback(
    async (slot: ApplicationDocumentSlot, file: File) => {
      return uploadDocument(slot, file);
    },
    [uploadDocument],
  );

  const deleteDocument = useCallback(
    async (documentId: string) => {
      setError(null);
      try {
        await DocumentService.delete(documentId, applicationId);
        await refresh();
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Delete failed';
        setError(message);
        throw err;
      }
    },
    [applicationId, refresh],
  );

  const previewDocument = useCallback(async (documentId: string) => {
    const url = await DocumentService.getPreviewUrl(documentId, applicationId);
    window.open(url, '_blank', 'noopener,noreferrer');
  }, [applicationId]);

  const slotDocuments = useMemo(
    () =>
      APPLICATION_DOCUMENT_SLOTS.map((slot) => ({
        slot,
        document: findDocumentForSlot(documents, slot),
      })),
    [documents],
  );

  const uploadedCount = slotDocuments.filter(({ document }) => Boolean(document)).length;
  const totalSlots = APPLICATION_DOCUMENT_SLOTS.length;

  return {
    documents,
    slotDocuments,
    isLoading,
    isUploading: uploadingSlot !== null,
    uploadingSlot,
    uploadProgress,
    uploadedCount,
    totalSlots,
    error,
    uploadDocument,
    replaceDocument,
    deleteDocument,
    previewDocument,
    refresh,
  };
}

export { findDocumentForSlot };
