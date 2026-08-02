'use client';

import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import {
  AlertCircle,
  ArrowLeft,
  Loader2,
  MapPin,
} from 'lucide-react';

import { ApplicationAnalysisSection } from '@/components/applications/ApplicationAnalysisSection';
import { ApplicationChatSection } from '@/components/applications/ApplicationChatSection';
import { ApplicationDocumentsSection } from '@/components/applications/ApplicationDocumentsSection';
import { Navigation } from '@/components/navigation';
import {
  APPLICATION_STATUS_LABELS,
  APPLICATION_TYPE_ICONS,
  APPLICATION_TYPE_LABELS,
} from '@/constants/applicationStatus';
import { useApplication } from '@/hooks/useApplication';
import { getApplicationDisplayName } from '@/lib/application-utils';

export default function ApplicationDetailsPage() {
  const params = useParams<{ applicationId: string }>();
  const router = useRouter();
  const applicationId = params.applicationId;

  const { application, isLoading, error, refresh } = useApplication(applicationId);

  if (isLoading) {
    return (
      <>
        <Navigation />
        <div className="min-h-screen flex items-center justify-center">
          <Loader2 className="animate-spin text-secondary" size={40} />
        </div>
      </>
    );
  }

  if (error || !application) {
    return (
      <>
        <Navigation />
        <div className="premium-dashboard-bg min-h-screen">
          <div className="relative z-20 py-16 px-4">
            <div className="max-w-lg mx-auto premium-card p-8 text-center space-y-4">
              <AlertCircle className="mx-auto text-red-400" size={40} />
              <h1 className="text-xl font-bold text-foreground">Application not found</h1>
              <p className="text-muted-foreground text-sm">
                {error ?? 'This application may have been deleted or you do not have access.'}
              </p>
              <button
                type="button"
                onClick={() => router.push('/dashboard')}
                className="inline-flex items-center gap-2 px-5 py-2.5 btn-gradient-primary text-background rounded-lg font-semibold text-sm"
              >
                <ArrowLeft size={16} />
                Back to Dashboard
              </button>
            </div>
          </div>
        </div>
      </>
    );
  }

  const typeIcon = APPLICATION_TYPE_ICONS[application.application_type];
  const typeLabel = APPLICATION_TYPE_LABELS[application.application_type];
  const statusLabel = APPLICATION_STATUS_LABELS[application.status];

  return (
    <>
      <Navigation />
      <div className="premium-dashboard-bg min-h-screen">
        <div className="noise-texture" />
        <div className="subtle-grid" />
        <div className="floating-light-emerald" style={{ top: '10%', left: '-10%' }} />
        <div className="floating-light-cyan" style={{ top: '40%', right: '-5%' }} />

        <div className="relative z-20 py-8 px-4 sm:px-6 lg:px-8">
          <div className="max-w-5xl mx-auto space-y-8">
            <div className="flex items-center justify-between gap-4 flex-wrap">
              <Link
                href="/dashboard"
                className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                <ArrowLeft size={16} />
                Back to Dashboard
              </Link>
              <p className="text-xs text-muted-foreground">
                Created{' '}
                {new Date(application.created_at).toLocaleDateString(undefined, {
                  year: 'numeric',
                  month: 'short',
                  day: 'numeric',
                })}
              </p>
            </div>

            <div className="premium-card card-animate-in p-8 space-y-6">
              <div className="flex items-start justify-between gap-4 flex-wrap">
                <div className="flex items-start gap-4 min-w-0">
                  <span className="text-4xl flex-shrink-0">{typeIcon}</span>
                  <div className="min-w-0">
                    <h1 className="text-3xl font-bold text-foreground truncate">
                      {getApplicationDisplayName(application)}
                    </h1>
                    <p className="text-muted-foreground mt-1">{typeLabel}</p>
                  </div>
                </div>
                <span className="px-3 py-1.5 rounded-full text-sm font-medium bg-secondary/20 text-secondary flex-shrink-0">
                  {statusLabel}
                </span>
              </div>

              <div className="animated-gradient-line" />

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">
                    Title
                  </p>
                  <p className="font-semibold text-foreground">
                    {getApplicationDisplayName(application)}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">
                    Country
                  </p>
                  <p className="font-semibold text-foreground flex items-center gap-2">
                    <MapPin size={14} className="text-secondary flex-shrink-0" />
                    {application.country || '—'}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">
                    Type
                  </p>
                  <p className="font-semibold text-foreground">{typeLabel}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">
                    Status
                  </p>
                  <p className="font-semibold text-foreground">{statusLabel}</p>
                </div>
              </div>

              <div className="pt-2 space-y-3">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Progress</span>
                  <span className="font-semibold text-foreground">
                    {application.readiness_score != null
                      ? `${application.readiness_score}% readiness`
                      : 'Upload documents to track progress'}
                  </span>
                </div>
                {application.readiness_score != null && (
                  <div className="h-3 rounded-full bg-muted/50 overflow-hidden progress-circle-glow">
                    <div
                      className="h-full btn-gradient-primary transition-all duration-500"
                      style={{ width: `${application.readiness_score}%` }}
                    />
                  </div>
                )}
              </div>
            </div>

            <ApplicationDocumentsSection applicationId={applicationId} />

            <ApplicationAnalysisSection
              applicationId={applicationId}
              onAnalysisComplete={refresh}
            />

            <ApplicationChatSection applicationId={applicationId} />
          </div>
        </div>
      </div>
    </>
  );
}
