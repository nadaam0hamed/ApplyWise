'use client'

import { useRouter } from 'next/navigation'
import { Navigation } from '@/components/navigation'
import { useAuth } from '@/hooks/useAuth'
import { useApplication } from '@/hooks/useApplication'
import {
  APPLICATION_STATUS_LABELS,
  APPLICATION_TYPE_LABELS,
  APPLICATION_TYPE_ICONS,
} from '@/constants/applicationStatus'
import {
  getApplicationDisplayName,
} from '@/lib/application-utils'
import {
  FileUp,
  Plus,
  MapPin,
  Loader2,
  AlertCircle,
} from 'lucide-react'

export default function DashboardPage() {
  const router = useRouter()
  const { user } = useAuth()
  const { applications, isLoading, error, refresh } = useApplication()

  const goToStartApplication = () => {
    router.push('/dashboard/start-application')
  }

  const displayName = user?.fullName ?? user?.email.split('@')[0] ?? 'there'
  const hasApplications = applications.length > 0

  return (
    <>
      <Navigation />
      <div className="premium-dashboard-bg">
        <div className="noise-texture" />
        <div className="subtle-grid" />
        <div className="floating-light-emerald" style={{ top: '15%', left: '-10%' }} />
        <div className="floating-light-cyan" style={{ top: '50%', right: '-5%' }} />
        <div className="floating-light-blue" style={{ bottom: '10%', left: '5%' }} />

        <div className="relative z-20 py-8 px-4 sm:px-6 lg:px-8">
          <div className="max-w-7xl mx-auto space-y-8">
            {/* Welcome */}
            <div className="premium-card card-animate-in overflow-hidden">
              <div className="p-6 sm:p-8 space-y-4">
                <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold text-foreground">
                  Welcome back, {displayName}! 👋
                </h1>
                <div className="animated-gradient-line" />
              </div>
            </div>

            {error && (
              <div className="premium-card p-6 border border-red-500/30 bg-red-500/10 flex items-start gap-3">
                <AlertCircle className="text-red-400 flex-shrink-0 mt-0.5" size={20} />
                <div>
                  <p className="font-semibold text-foreground">Failed to load applications</p>
                  <p className="text-sm text-muted-foreground mt-1">{error}</p>
                  <button
                    type="button"
                    onClick={() => refresh()}
                    className="text-sm text-secondary hover:text-secondary/80 mt-2 transition-colors"
                  >
                    Try again
                  </button>
                </div>
              </div>
            )}

            {isLoading ? (
              <div className="premium-card p-16 flex flex-col items-center justify-center gap-4">
                <Loader2 className="animate-spin text-secondary" size={40} />
                <p className="text-muted-foreground">Loading your applications...</p>
              </div>
            ) : !hasApplications ? (
              /* Empty state — no readiness, documents, analysis, or timeline */
              <div className="premium-card p-8 sm:p-12 md:p-16 card-animate-in text-center space-y-6">
                <div className="mx-auto w-16 h-16 sm:w-20 sm:h-20 rounded-full bg-secondary/10 flex items-center justify-center">
                  <FileUp className="text-secondary w-7 h-7 sm:w-9 sm:h-9" />
                </div>
                <div className="space-y-2">
                  <h2 className="text-xl sm:text-2xl font-bold text-foreground">No applications yet</h2>
                  <p className="text-muted-foreground max-w-md mx-auto text-sm sm:text-base">
                    Start your first application to track scholarships, university admissions,
                    visas, and more — all in one place.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={goToStartApplication}
                  className="relative z-10 inline-flex items-center gap-3 px-8 py-3 sm:px-10 sm:py-4 btn-gradient-primary text-background rounded-xl font-semibold text-base sm:text-lg hover:shadow-lg hover:shadow-primary/30 transition-all cursor-pointer pointer-events-auto"
                >
                  <Plus className="w-4 h-4 sm:w-5 sm:h-5" />
                  Create Application
                </button>
              </div>
            ) : (
              /* Applications list — real Supabase data only */
              <div className="space-y-6">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                  <h2 className="text-lg sm:text-xl font-bold text-foreground">Your Applications</h2>
                  <button
                    type="button"
                    onClick={goToStartApplication}
                    className="relative z-10 inline-flex items-center justify-center gap-2 px-4 sm:px-5 py-2 sm:py-2.5 btn-gradient-primary text-background rounded-lg font-semibold hover:shadow-lg hover:shadow-primary/30 transition-all text-sm cursor-pointer pointer-events-auto"
                  >
                    <Plus className="w-4 h-4 sm:w-5 sm:h-5" />
                    <span className="hidden sm:inline">Create Application</span>
                    <span className="sm:hidden">Create</span>
                  </button>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
                  {applications.map((app, index) => {
                    const typeIcon = APPLICATION_TYPE_ICONS[app.application_type]
                    const typeLabel = APPLICATION_TYPE_LABELS[app.application_type]
                    const statusLabel = APPLICATION_STATUS_LABELS[app.status]

                    return (
                      <button
                        key={app.id}
                        type="button"
                        onClick={() => router.push(`/applications/${app.id}`)}
                        className="premium-card p-4 sm:p-6 card-animate-in space-y-3 sm:space-y-4 text-left w-full hover:border-secondary/30 transition-all cursor-pointer"
                        style={{ animationDelay: `${index * 0.05}s` }}
                      >
                        <div className="flex items-start justify-between gap-2 sm:gap-3">
                          <div className="flex items-center gap-2 sm:gap-3 min-w-0">
                            <span className="text-xl sm:text-2xl flex-shrink-0">{typeIcon}</span>
                            <div className="min-w-0">
                              <h3 className="font-semibold text-foreground truncate text-sm sm:text-base">
                                {getApplicationDisplayName(app)}
                              </h3>
                              <p className="text-[10px] sm:text-xs text-muted-foreground">{typeLabel}</p>
                            </div>
                          </div>
                          <span className="px-2 py-0.5 sm:px-2.5 sm:py-1 rounded-full text-[10px] sm:text-xs font-medium bg-secondary/20 text-secondary flex-shrink-0">
                            {statusLabel}
                          </span>
                        </div>

                        <div className="space-y-2 text-sm">
                          {app.country && (
                            <div className="flex items-center gap-2 text-muted-foreground">
                              <MapPin size={14} className="flex-shrink-0" />
                              <span>{app.country}</span>
                            </div>
                          )}
                        </div>

                        {app.readiness_score !== null && app.readiness_score !== undefined && (
                          <div className="pt-3 border-t border-secondary/20">
                            <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">
                              Readiness Score
                            </p>
                            <p className="text-2xl font-bold text-foreground">
                              {app.readiness_score}%
                            </p>
                          </div>
                        )}

                        <p className="text-xs text-muted-foreground">
                          Created{' '}
                          {new Date(app.created_at).toLocaleDateString(undefined, {
                            year: 'numeric',
                            month: 'short',
                            day: 'numeric',
                          })}
                        </p>
                      </button>
                    )
                  })}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  )
}
