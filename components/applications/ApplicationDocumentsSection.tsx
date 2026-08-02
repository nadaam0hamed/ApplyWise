'use client';

import { useRef, useState } from 'react';
import {
  CheckCircle2,
  Eye,
  FileText,
  Loader2,
  Trash2,
  Upload,
  AlertCircle,
} from 'lucide-react';

import {
  SUPPORTED_FILE_EXTENSIONS,
  type ApplicationDocumentSlot,
} from '@/constants/documentTypes';
import { useDocuments } from '@/hooks/useDocuments';
import type { Document } from '@/types/document';

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

type DocumentSlotRowProps = {
  slot: ApplicationDocumentSlot;
  document: Document | undefined;
  isUploading: boolean;
  progress: number;
  onUpload: (slot: ApplicationDocumentSlot, file: File) => Promise<void>;
  onDelete: (documentId: string) => Promise<void>;
  onPreview: (documentId: string) => Promise<void>;
};

function DocumentSlotRow({
  slot,
  document,
  isUploading,
  progress,
  onUpload,
  onDelete,
  onPreview,
}: DocumentSlotRowProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isPreviewing, setIsPreviewing] = useState(false);

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (!file) return;

    setActionError(null);
    try {
      await onUpload(slot, file);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Upload failed');
    }
  };

  const handleDelete = async () => {
    if (!document) return;
    if (!window.confirm(`Delete ${slot.label}?`)) return;

    setIsDeleting(true);
    setActionError(null);
    try {
      await onDelete(document.id);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Delete failed');
    } finally {
      setIsDeleting(false);
    }
  };

  const handlePreview = async () => {
    if (!document) return;

    setIsPreviewing(true);
    setActionError(null);
    try {
      await onPreview(document.id);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Preview failed');
    } finally {
      setIsPreviewing(false);
    }
  };

  const isUploaded = Boolean(document);

  return (
    <div className="premium-card p-5 space-y-4">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3 min-w-0">
          <div
            className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${
              isUploaded ? 'bg-secondary/20' : 'bg-muted/40'
            }`}
          >
            {isUploaded ? (
              <CheckCircle2 className="text-secondary" size={20} />
            ) : (
              <FileText className="text-muted-foreground" size={20} />
            )}
          </div>
          <div className="min-w-0">
            <h3 className="font-semibold text-foreground">{slot.label}</h3>
            {isUploaded && document ? (
              <p className="text-sm text-muted-foreground truncate mt-0.5">
                {document.file_name} · {formatFileSize(document.file_size)}
              </p>
            ) : (
              <p className="text-sm text-muted-foreground mt-0.5">
                PDF, DOCX, PNG, or JPEG
              </p>
            )}
          </div>
        </div>

        <span
          className={`px-2.5 py-1 rounded-full text-xs font-medium flex-shrink-0 ${
            isUploaded
              ? 'bg-secondary/20 text-secondary'
              : 'bg-muted/50 text-muted-foreground'
          }`}
        >
          {isUploaded ? 'Uploaded' : 'Missing'}
        </span>
      </div>

      {isUploading && (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>Uploading…</span>
            <span>{progress}%</span>
          </div>
          <div className="h-2 rounded-full bg-muted/50 overflow-hidden">
            <div
              className="h-full btn-gradient-primary transition-all duration-200"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {actionError && (
        <p className="text-xs text-red-400">{actionError}</p>
      )}

      <div className="flex flex-wrap gap-2">
        <input
          ref={inputRef}
          type="file"
          accept={SUPPORTED_FILE_EXTENSIONS.map((ext) => `.${ext}`).join(',')}
          className="hidden"
          onChange={handleFileChange}
        />

        <button
          type="button"
          disabled={isUploading || isDeleting}
          onClick={() => inputRef.current?.click()}
          className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg btn-gradient-primary text-background hover:shadow-lg hover:shadow-primary/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isUploading ? (
            <Loader2 size={16} className="animate-spin" />
          ) : (
            <Upload size={16} />
          )}
          {isUploaded ? 'Replace' : 'Upload'}
        </button>

        {isUploaded && document && (
          <>
            <button
              type="button"
              disabled={isUploading || isDeleting || isPreviewing}
              onClick={handlePreview}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg border border-secondary/30 text-foreground hover:border-secondary transition-colors disabled:opacity-50"
            >
              {isPreviewing ? (
                <Loader2 size={16} className="animate-spin" />
              ) : (
                <Eye size={16} />
              )}
              Preview
            </button>

            <button
              type="button"
              disabled={isUploading || isDeleting || isPreviewing}
              onClick={handleDelete}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg border border-red-500/30 text-red-400 hover:border-red-500/60 transition-colors disabled:opacity-50"
            >
              {isDeleting ? (
                <Loader2 size={16} className="animate-spin" />
              ) : (
                <Trash2 size={16} />
              )}
              Delete
            </button>
          </>
        )}
      </div>
    </div>
  );
}

type ApplicationDocumentsSectionProps = {
  applicationId: string;
};

export function ApplicationDocumentsSection({
  applicationId,
}: ApplicationDocumentsSectionProps) {
  const {
    slotDocuments,
    isLoading,
    uploadingSlot,
    uploadProgress,
    uploadedCount,
    totalSlots,
    error,
    uploadDocument,
    deleteDocument,
    previewDocument,
  } = useDocuments(applicationId);

  const documentProgress =
    totalSlots > 0 ? Math.round((uploadedCount / totalSlots) * 100) : 0;

  if (isLoading) {
    return (
      <div className="premium-card p-8 flex items-center justify-center gap-3">
        <Loader2 className="animate-spin text-secondary" size={24} />
        <span className="text-muted-foreground">Loading documents…</span>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="premium-card p-6 space-y-3">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <h2 className="text-xl font-bold text-foreground">Documents</h2>
          <span className="text-sm font-medium text-secondary">
            {uploadedCount}/{totalSlots} uploaded · {documentProgress}%
          </span>
        </div>
        <div className="h-2 rounded-full bg-muted/50 overflow-hidden">
          <div
            className="h-full btn-gradient-primary transition-all duration-500"
            style={{ width: `${documentProgress}%` }}
          />
        </div>
        <p className="text-sm text-muted-foreground">
          Upload required files for your application
        </p>
      </div>

      {error && (
        <div className="premium-card p-4 border border-red-500/30 bg-red-500/10 flex items-start gap-3">
          <AlertCircle className="text-red-400 flex-shrink-0 mt-0.5" size={18} />
          <p className="text-sm text-red-400">{error}</p>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {slotDocuments.map(({ slot, document }) => (
          <DocumentSlotRow
            key={slot.key}
            slot={slot}
            document={document}
            isUploading={uploadingSlot === slot.key}
            progress={uploadProgress[slot.key] ?? 0}
            onUpload={async (s, file) => {
              await uploadDocument(s, file);
            }}
            onDelete={deleteDocument}
            onPreview={previewDocument}
          />
        ))}
      </div>
    </div>
  );
}
