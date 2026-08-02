'use client';

import { useState } from 'react';

import {
  APPLICATION_STATUS_LABELS,
  APPLICATION_STATUSES,
  APPLICATION_TYPE_LABELS,
  APPLICATION_TYPES,
  ApplicationStatus,
  ApplicationType,
} from '@/constants/applicationStatus';
import type { Application, ApplicationUpdate } from '@/types/application';

type ApplicationFormProps = {
  initialValues?: Partial<Application>;
  onSubmit: (values: ApplicationUpdate) => Promise<void>;
  onCancel?: () => void;
  submitLabel?: string;
  isEditing?: boolean;
};

type FormState = {
  application_type: ApplicationType;
  status: ApplicationStatus;
  title: string;
  country: string;
  source_url: string;
};

function toFormState(application?: Partial<Application>): FormState {
  return {
    application_type: application?.application_type ?? ApplicationType.Scholarship,
    status: application?.status ?? ApplicationStatus.InProgress,
    title: application?.title ?? '',
    country: application?.country ?? '',
    source_url: application?.source_url ?? '',
  };
}

export function ApplicationForm({
  initialValues,
  onSubmit,
  onCancel,
  submitLabel = 'Save Application',
  isEditing = false,
}: ApplicationFormProps) {
  const [form, setForm] = useState<FormState>(() => toFormState(initialValues));
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleChange = (field: keyof FormState, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      await onSubmit({
        application_type: form.application_type,
        status: form.status,
        title: form.title.trim() || null,
        country: form.country.trim() || null,
        source_url: form.source_url.trim() || null,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save application');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {error && (
        <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-xs text-muted-foreground uppercase tracking-wide mb-2">
            Application Type
          </label>
          <select
            value={form.application_type}
            onChange={(e) => handleChange('application_type', e.target.value)}
            disabled={isEditing}
            className="w-full px-4 py-3 rounded-lg bg-background border border-secondary/30 text-foreground focus:border-secondary focus:outline-none transition-colors disabled:opacity-60"
          >
            {APPLICATION_TYPES.map((type) => (
              <option key={type} value={type}>
                {APPLICATION_TYPE_LABELS[type]}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs text-muted-foreground uppercase tracking-wide mb-2">
            Status
          </label>
          <select
            value={form.status}
            onChange={(e) => handleChange('status', e.target.value)}
            className="w-full px-4 py-3 rounded-lg bg-background border border-secondary/30 text-foreground focus:border-secondary focus:outline-none transition-colors"
          >
            {APPLICATION_STATUSES.map((status) => (
              <option key={status} value={status}>
                {APPLICATION_STATUS_LABELS[status]}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div>
        <label className="block text-xs text-muted-foreground uppercase tracking-wide mb-2">
          Title
        </label>
        <input
          type="text"
          value={form.title}
          onChange={(e) => handleChange('title', e.target.value)}
          placeholder="e.g. Erasmus Mundus Master's Program"
          className="w-full px-4 py-3 rounded-lg bg-background border border-secondary/30 text-foreground placeholder-muted-foreground focus:border-secondary focus:outline-none transition-colors"
        />
      </div>

      <div>
        <label className="block text-xs text-muted-foreground uppercase tracking-wide mb-2">
          Country
        </label>
        <input
          type="text"
          value={form.country}
          onChange={(e) => handleChange('country', e.target.value)}
          className="w-full px-4 py-3 rounded-lg bg-background border border-secondary/30 text-foreground placeholder-muted-foreground focus:border-secondary focus:outline-none transition-colors"
        />
      </div>

      <div>
        <label className="block text-xs text-muted-foreground uppercase tracking-wide mb-2">
          Source URL
        </label>
        <input
          type="url"
          value={form.source_url}
          onChange={(e) => handleChange('source_url', e.target.value)}
          placeholder="https://example.com/requirements"
          className="w-full px-4 py-3 rounded-lg bg-background border border-secondary/30 text-foreground placeholder-muted-foreground focus:border-secondary focus:outline-none transition-colors"
        />
      </div>

      <div className="flex gap-4">
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            disabled={isSubmitting}
            className="flex-1 px-6 py-3 rounded-lg border border-secondary/30 text-secondary hover:bg-secondary/10 transition-colors font-semibold disabled:opacity-50"
          >
            Cancel
          </button>
        )}
        <button
          type="submit"
          disabled={isSubmitting}
          className="flex-1 px-6 py-3 btn-gradient-primary text-background rounded-lg font-semibold hover:shadow-lg hover:shadow-primary/30 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {isSubmitting ? (
            <>
              <div className="w-4 h-4 border-2 border-background border-t-transparent rounded-full animate-spin" />
              Saving...
            </>
          ) : (
            submitLabel
          )}
        </button>
      </div>
    </form>
  );
}
