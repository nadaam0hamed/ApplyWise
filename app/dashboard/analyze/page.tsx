'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import { Navigation } from '@/components/navigation'
import { MultiAgentPipeline } from '@/components/multi-agent-pipeline'
import { ApplicationAnalysisSection } from '@/components/applications/ApplicationAnalysisSection'

export default function AnalyzePage() {
  const params = useParams()
  const applicationId = params.applicationId as string
  const [analyzing, setAnalyzing] = useState(true)

  const handleAnalysisComplete = () => {
    setAnalyzing(false)
  }

  if (analyzing) {
    return (
      <>
        <Navigation />
        <MultiAgentPipeline onComplete={handleAnalysisComplete} />
      </>
    )
  }

  return (
    <>
      <Navigation />
      <div className="min-h-screen bg-gradient-to-b from-background via-background to-background py-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-6xl mx-auto space-y-8">
          {/* Header */}
          <div className="flex items-center justify-between">
            <h1 className="text-3xl font-bold text-foreground">Analysis Results</h1>
            <Link
              href="/dashboard"
              className="px-4 py-2 text-sm text-muted-foreground hover:text-foreground transition"
            >
              ← Back to Dashboard
            </Link>
          </div>

          {/* Analysis Section */}
          <ApplicationAnalysisSection applicationId={applicationId} />
        </div>
      </div>
    </>
  )
}
