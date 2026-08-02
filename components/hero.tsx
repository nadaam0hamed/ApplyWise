'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'

import { APPLICATION_STATUS_LABELS, ApplicationStatus } from '@/constants/applicationStatus'
import { useAuth } from '@/hooks/useAuth'
import { ApplicationService } from '@/services/application.service'
import type { Application } from '@/types/application'

const SCORE_CIRCLE_RADIUS = 40
const SCORE_CIRCUMFERENCE = 2 * Math.PI * SCORE_CIRCLE_RADIUS

function getPreviewStatus(application: Application | null): { label: string; description: string } {
  if (!application) {
    return {
      label: 'Getting Started',
      description: 'Create your first application to begin tracking progress.',
    }
  }

  const label = APPLICATION_STATUS_LABELS[application.status]

  switch (application.status) {
    case ApplicationStatus.Draft:
      return { label, description: 'Continue building your application.' }
    case ApplicationStatus.InProgress:
      return { label, description: "Good progress! You're almost there." }
    case ApplicationStatus.Analyzing:
      return { label, description: 'AI is reviewing your application.' }
    case ApplicationStatus.Ready:
      return { label, description: 'Your application is ready to submit.' }
    case ApplicationStatus.Submitted:
      return { label, description: 'Your application has been submitted.' }
    case ApplicationStatus.Accepted:
      return { label, description: 'Congratulations on your acceptance!' }
    case ApplicationStatus.Rejected:
      return { label, description: 'Review feedback and plan your next steps.' }
    default:
      return { label, description: "Let's make your application perfect." }
  }
}

export function Hero() {
  const { user, loading } = useAuth()
  const router = useRouter()
  const [latestApplication, setLatestApplication] = useState<Application | null>(null)

  const isAuthenticated = !!user
  const showDashboardPreview = !loading && isAuthenticated

  useEffect(() => {
    if (!user) {
      setLatestApplication(null)
      return
    }

    let mounted = true

    ApplicationService.getLatestForUser()
      .then((application) => {
        if (mounted) {
          setLatestApplication(application)
        }
      })
      .catch(() => {
        if (mounted) {
          setLatestApplication(null)
        }
      })

    return () => {
      mounted = false
    }
  }, [user])

  const displayName = user?.fullName ?? user?.email?.split('@')[0] ?? 'there'
  const readinessScore = latestApplication?.readiness_score
  const hasReadinessScore = readinessScore != null
  const scoreDisplay = hasReadinessScore ? `${readinessScore}%` : '—'
  const scoreStrokeOffset = hasReadinessScore
    ? SCORE_CIRCUMFERENCE * (1 - readinessScore / 100)
    : SCORE_CIRCUMFERENCE
  const previewStatus = getPreviewStatus(latestApplication)
  const previewSubtitle = latestApplication
    ? "Let's make your application perfect."
    : 'Start your first application to unlock your dashboard.'

  const handlePrimaryClick = () => {
    if (isAuthenticated) {
      router.push('/dashboard')
    } else {
      router.push('/login')
    }
  }

  return (
    <>
      {/* Hero Section with Cinematic Background */}
      <section id="home" className="relative min-h-screen overflow-hidden hero-background flex items-center">
        {/* Premium Dark Overlay */}
        <div className="absolute inset-0 hero-overlay -z-10"></div>

        <div className="max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-20 lg:py-32 z-10 relative">
          <div
            className={
              showDashboardPreview
                ? 'grid grid-cols-1 lg:grid-cols-2 gap-12 items-center'
                : 'max-w-3xl'
            }
          >
            {/* Left Content */}
            <div className="flex flex-col space-y-8">
              {/* Badge */}
              <div className="inline-flex items-center gap-3 w-fit px-4 py-2 rounded-full bg-secondary/10 border border-secondary/30 backdrop-blur-sm">
                <span className="relative flex h-2 w-2">
                  <span className="absolute inline-flex h-full w-full rounded-full bg-secondary/70 animate-pulse"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-secondary"></span>
                </span>
                <span className="text-sm font-medium text-secondary">AI-Powered • Smart • Trusted</span>
              </div>

              {/* Main Headline */}
              <div className="space-y-4">
                <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold leading-tight tracking-tight">
                  <span className="text-white block">Your Journey.</span>
                  <span className="block text-transparent bg-clip-text bg-gradient-to-r from-secondary via-cyan-400 to-emerald-400 mt-2">
                    Our Intelligence.
                  </span>
                </h1>
              </div>

              {/* Tagline */}
              <div className="space-y-4">
                <p className="text-xl font-semibold text-secondary">Apply Smarter. Stress Less.</p>
                <p className="text-lg leading-relaxed text-muted-foreground max-w-xl">
                  Upload your documents, let AI analyze your application, identify what's missing, build your timeline, and answer your questions instantly.
                </p>
              </div>

              {/* CTA Buttons */}
              <div className="flex flex-col sm:flex-row gap-4 pt-8">
                <button
                  type="button"
                  onClick={handlePrimaryClick}
                  disabled={loading}
                  className="group flex items-center justify-center gap-2 px-8 py-4 btn-gradient-primary text-foreground rounded-lg font-semibold hover:shadow-lg transition-all duration-300 hover:scale-105 disabled:opacity-60 disabled:hover:scale-100"
                >
                  <span>{loading ? 'Loading...' : isAuthenticated ? 'My Dashboard' : 'Get Started'}</span>
                  <svg className="w-5 h-5 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                  </svg>
                </button>
              </div>
            </div>

            {/* Right: Premium Dashboard Mockup — authenticated users only */}
            {showDashboardPreview && (
              <div className="relative hidden lg:block h-[600px]">
                {/* Main Dashboard Card - Glassmorphism */}
                <div className="absolute inset-0 glassmorphism rounded-2xl p-6 overflow-hidden glow-emerald">
                  {/* Header */}
                  <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-3">
                      <img
                        src="/applywise-logo.png"
                        alt="ApplyWise"
                        className="w-8 h-8 object-contain"
                      />
                      <span className="font-semibold text-foreground">ApplyWise</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <button className="w-9 h-9 rounded-lg bg-secondary/20 hover:bg-secondary/30 flex items-center justify-center transition-colors">
                        <span className="text-lg">🔔</span>
                      </button>
                      <div className="w-9 h-9 rounded-full bg-gradient-emerald-cyan"></div>
                    </div>
                  </div>

                  {/* Welcome Section */}
                  <div className="mb-6">
                    <h3 className="text-xl font-bold text-foreground">Welcome back, {displayName}! 👋</h3>
                    <p className="text-sm text-muted-foreground">{previewSubtitle}</p>
                  </div>

                  {/* Main Grid */}
                  <div className="grid grid-cols-2 gap-6">
                    {/* Left Sidebar Navigation */}
                    <div className="border-r border-secondary/20 pr-4 space-y-2">
                      <div className="flex items-center gap-3 px-3 py-2 rounded-lg bg-secondary/15">
                        <span className="text-lg">📊</span>
                        <span className="text-sm font-medium text-foreground">Dashboard</span>
                      </div>
                      {[
                        { icon: '📄', label: 'Documents' },
                        { icon: '✅', label: 'Checklist' },
                        { icon: '📅', label: 'Timeline' },
                        { icon: '🤖', label: 'AI Assistant' },
                      ].map((item) => (
                        <div key={item.label} className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-secondary/10 cursor-pointer transition-colors">
                          <span className="text-lg">{item.icon}</span>
                          <span className="text-sm text-muted-foreground">{item.label}</span>
                        </div>
                      ))}
                    </div>

                    {/* Right Content */}
                    <div className="space-y-4">
                      {/* Readiness Score */}
                      <div>
                        <p className="text-sm font-semibold text-foreground mb-2">Readiness Score</p>
                        <div className="flex justify-center">
                          <div className="relative w-24 h-24">
                            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                              <circle cx="50" cy="50" r={SCORE_CIRCLE_RADIUS} fill="none" stroke="#1a2a35" strokeWidth="5" />
                              <circle
                                cx="50"
                                cy="50"
                                r={SCORE_CIRCLE_RADIUS}
                                fill="none"
                                stroke="url(#scoreGradient)"
                                strokeWidth="5"
                                strokeDasharray={SCORE_CIRCUMFERENCE}
                                strokeDashoffset={scoreStrokeOffset}
                                strokeLinecap="round"
                              />
                              <defs>
                                <linearGradient id="scoreGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                                  <stop offset="0%" stopColor="#0F766E" />
                                  <stop offset="100%" stopColor="#14B8A6" />
                                </linearGradient>
                              </defs>
                            </svg>
                            <div className="absolute inset-0 flex items-center justify-center">
                              <span className="text-2xl font-bold text-foreground">{scoreDisplay}</span>
                            </div>
                          </div>
                        </div>
                        {!hasReadinessScore && (
                          <p className="text-xs text-muted-foreground text-center mt-2">
                            Run an analysis to see your score
                          </p>
                        )}
                      </div>

                      {/* Status Info */}
                      <div className="bg-secondary/10 rounded-lg p-3 border border-secondary/20">
                        <p className="text-xs font-semibold text-secondary mb-1">{previewStatus.label}</p>
                        <p className="text-xs text-muted-foreground">{previewStatus.description}</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Smooth Transition Gradient to Next Section */}
        <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-b from-transparent to-background pointer-events-none"></div>
      </section>

      {/* Spacer to ensure smooth transition */}
      <div className="h-8 bg-gradient-to-b from-background to-background"></div>
    </>
  )
}
