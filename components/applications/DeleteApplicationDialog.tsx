'use client';

import { AlertTriangle } from 'lucide-react';

import { getApplicationDisplayName } from '@/lib/application-utils';
import type { Application } from '@/types/application';

type DeleteApplicationDialogProps = {
  application: Application;
  isOpen: boolean;
  isDeleting: boolean;
  error: string | null;
  onConfirm: () => void;
  onCancel: () => void;
};

export function DeleteApplicationDialog({
  application,
  isOpen,
  isDeleting,
  error,
  onConfirm,
  onCancel,
}: DeleteApplicationDialogProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={isDeleting ? undefined : onCancel}
      />
      <div className="relative premium-card p-8 max-w-md w-full space-y-6">
        <div className="flex items-start gap-4">
          <div className="p-3 rounded-full bg-red-500/10">
            <AlertTriangle className="text-red-400" size={24} />
          </div>
          <div>
            <h2 className="text-xl font-bold text-foreground">Delete Application</h2>
            <p className="text-sm text-muted-foreground mt-2">
              Are you sure you want to delete{' '}
              <span className="font-semibold text-foreground">
                {getApplicationDisplayName(application)}
              </span>
              ? This will permanently remove all associated requirements, documents, and timeline
              events.
            </p>
          </div>
        </div>

        {error && (
          <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
            {error}
          </div>
        )}

        <div className="flex gap-3">
          <button
            type="button"
            onClick={onCancel}
            disabled={isDeleting}
            className="flex-1 px-4 py-3 rounded-lg border border-secondary/30 text-secondary hover:bg-secondary/10 transition-colors font-semibold disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={isDeleting}
            className="flex-1 px-4 py-3 rounded-lg bg-red-600 text-white font-semibold hover:bg-red-700 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {isDeleting ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Deleting...
              </>
            ) : (
              'Delete'
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
