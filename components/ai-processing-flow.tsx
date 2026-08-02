'use client'

import { useState, useEffect } from 'react'
import { CheckCircle, Loader2 } from 'lucide-react'

interface ProcessingStage {
  id: string
  title: string
  icon: string
  substeps?: string[]
  duration: number
}

interface AIProcessingFlowProps {
  documentCount: number
  onComplete: () => void
}

const PROCESSING_STAGES: ProcessingStage[] = [
  {
    id: 'reading',
    title: 'Reading uploaded documents...',
    icon: '📄',
    duration: 2000,
  },
  {
    id: 'detecting',
    title: 'Detecting document types...',
    icon: '🔍',
    duration: 1500,
  },
  {
    id: 'extracting',
    title: 'Extracting structured information...',
    icon: '🧠',
    duration: 2000,
  },
  {
    id: 'searching',
    title: 'Searching official knowledge base...',
    icon: '📚',
    duration: 2000,
  },
  {
    id: 'comparing',
    title: 'Comparing uploaded documents...',
    icon: '⚖️',
    duration: 1500,
  },
  {
    id: 'checking',
    title: 'Checking for missing documents...',
    icon: '❗',
    duration: 1000,
  },
  {
    id: 'building',
    title: 'Building personalized checklist...',
    icon: '📋',
    duration: 1000,
  },
  {
    id: 'timeline',
    title: 'Generating submission timeline...',
    icon: '📅',
    duration: 1000,
  },
  {
    id: 'readiness',
    title: 'Calculating readiness score...',
    icon: '📊',
    duration: 1500,
  },
  {
    id: 'recommendations',
    title: 'Generating AI recommendations...',
    icon: '🤖',
    duration: 1500,
  },
]

// Document detection substeps
const DOCUMENT_DETECTIONS = [
  'Passport detected',
  'CV detected',
  'Transcript detected',
  'IELTS Score detected',
]

// Comparison substeps
const COMPARISON_STEPS = [
  'Checking Passport...',
  'Checking Transcript...',
  'Checking CV...',
  'Checking IELTS...',
  'Checking Recommendation Letter...',
]

// Extraction fields
const EXTRACTION_FIELDS = [
  'Name',
  'University',
  'Nationality',
  'Degree',
  'Passport Number',
  'Graduation Year',
]

// Knowledge base searches
const KNOWLEDGE_BASE_SEARCHES = [
  'Retrieving scholarship requirements...',
  'Retrieving university requirements...',
  'Retrieving visa requirements...',
]

export function AIProcessingFlow({ documentCount, onComplete }: AIProcessingFlowProps) {
  const [currentStageIndex, setCurrentStageIndex] = useState(0)
  const [progress, setProgress] = useState(0)
  const [currentSubstepIndex, setCurrentSubstepIndex] = useState(0)
  const [completedStages, setCompletedStages] = useState<string[]>([])

  // Calculate duration based on document count
  const getDurationMultiplier = () => {
    if (documentCount === 1) return 1
    if (documentCount <= 3) return 1.3
    if (documentCount <= 6) return 1.6
    return 2
  }

  const durationMultiplier = getDurationMultiplier()

  // Get substeps for current stage
  const getSubsteps = (stageId: string) => {
    switch (stageId) {
      case 'detecting':
        return DOCUMENT_DETECTIONS
      case 'extracting':
        return EXTRACTION_FIELDS
      case 'searching':
        return KNOWLEDGE_BASE_SEARCHES
      case 'comparing':
        return COMPARISON_STEPS
      default:
        return []
    }
  }

  const currentStage = PROCESSING_STAGES[currentStageIndex]
  const substeps = getSubsteps(currentStage.id)

  // Progress animation
  useEffect(() => {
    if (currentStageIndex >= PROCESSING_STAGES.length) {
      onComplete()
      return
    }

    const stageDuration = currentStage.duration * durationMultiplier

    // If this stage has substeps, distribute time among them
    if (substeps.length > 0) {
      const substepDuration = stageDuration / substeps.length

      const substepInterval = setInterval(() => {
        setCurrentSubstepIndex(prev => {
          if (prev + 1 >= substeps.length) {
            clearInterval(substepInterval)
            // Move to next stage
            setTimeout(() => {
              setCompletedStages(prev => [...prev, currentStage.id])
              setCurrentStageIndex(prev => prev + 1)
              setCurrentSubstepIndex(0)
            }, 300)
            return substeps.length - 1
          }
          return prev + 1
        })
      }, substepDuration)

      return () => clearInterval(substepInterval)
    } else {
      // No substeps, just advance after duration
      const timer = setTimeout(() => {
        setCompletedStages(prev => [...prev, currentStage.id])
        setCurrentStageIndex(prev => prev + 1)
      }, stageDuration)

      return () => clearTimeout(timer)
    }
  }, [currentStageIndex, currentStage.id, substeps.length, durationMultiplier])

  // Update progress bar
  useEffect(() => {
    const totalStages = PROCESSING_STAGES.length
    const baseProgress = (completedStages.length / totalStages) * 100
    const currentProgress =
      baseProgress + ((currentSubstepIndex + 1) / (substeps.length || 1)) * (100 / totalStages) * 0.5

    // Generate dynamic progress
    const dynamicProgress = Math.min(
      baseProgress + ((currentSubstepIndex + 1) / (substeps.length || 1)) * (100 / totalStages) * 0.8,
      96
    )

    setProgress(dynamicProgress)
  }, [completedStages.length, currentSubstepIndex, substeps.length])

  return (
    <div className="min-h-screen bg-gradient-to-b from-background via-background to-background py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-3xl font-bold text-foreground mb-2">Analyzing Your Documents</h1>
          <p className="text-muted-foreground">This may take a moment</p>
        </div>

        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-muted-foreground">Overall Progress</span>
            <span className="text-sm font-bold text-secondary">{Math.round(progress)}%</span>
          </div>
          <div className="w-full h-2 bg-secondary/20 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-primary to-secondary transition-all duration-300 shadow-lg shadow-secondary/40"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Processing Stages */}
        <div className="space-y-4">
          {PROCESSING_STAGES.map((stage, idx) => {
            const isCompleted = completedStages.includes(stage.id)
            const isActive = currentStageIndex === idx
            const isPending = idx > currentStageIndex

            return (
              <div
                key={stage.id}
                className={`transition-all duration-300 ${
                  isActive
                    ? 'scale-100 opacity-100'
                    : isPending
                      ? 'scale-95 opacity-40'
                      : 'scale-100 opacity-100'
                }`}
              >
                {/* Stage Header */}
                <div
                  className={`p-4 rounded-lg border transition-all ${
                    isCompleted
                      ? 'bg-secondary/10 border-secondary/40'
                      : isActive
                        ? 'bg-primary/10 border-primary/40'
                        : 'bg-secondary/5 border-secondary/20'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    {isCompleted ? (
                      <CheckCircle className="w-6 h-6 text-secondary flex-shrink-0 mt-0.5" />
                    ) : isActive ? (
                      <Loader2 className="w-6 h-6 text-primary flex-shrink-0 mt-0.5 animate-spin" />
                    ) : (
                      <span className="text-xl">{stage.icon}</span>
                    )}

                    <div className="flex-1">
                      <p
                        className={`font-medium transition-colors ${
                          isCompleted
                            ? 'text-muted-foreground line-through'
                            : 'text-foreground'
                        }`}
                      >
                        {stage.title}
                      </p>

                      {/* Substeps */}
                      {isActive && substeps.length > 0 && (
                        <div className="mt-3 space-y-2 ml-1">
                          {substeps.map((substep, substepIdx) => (
                            <div
                              key={substepIdx}
                              className={`flex items-center gap-2 text-sm transition-all duration-200 ${
                                substepIdx < currentSubstepIndex
                                  ? 'text-secondary opacity-60'
                                  : substepIdx === currentSubstepIndex
                                    ? 'text-foreground font-medium'
                                    : 'text-muted-foreground opacity-40'
                              }`}
                            >
                              <span className="w-1.5 h-1.5 rounded-full flex-shrink-0">
                                {substepIdx < currentSubstepIndex ? (
                                  <CheckCircle className="w-1.5 h-1.5 text-secondary" />
                                ) : substepIdx === currentSubstepIndex ? (
                                  <Loader2 className="w-1.5 h-1.5 text-foreground animate-spin" />
                                ) : (
                                  <div className="w-1.5 h-1.5 rounded-full bg-muted-foreground" />
                                )}
                              </span>
                              <span>✓ {substep}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Divider */}
                {idx < PROCESSING_STAGES.length - 1 && (
                  <div className="flex justify-center my-2">
                    <div className="w-0.5 h-3 bg-gradient-to-b from-secondary/20 to-transparent" />
                  </div>
                )}
              </div>
            )
          })}
        </div>

        {/* Final Message */}
        {completedStages.length === PROCESSING_STAGES.length && (
          <div className="mt-12 text-center">
            <div className="mb-4">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-secondary/20 border-2 border-secondary">
                <CheckCircle className="w-8 h-8 text-secondary animate-pulse" />
              </div>
            </div>
            <h2 className="text-xl font-bold text-foreground">Analysis Complete!</h2>
            <p className="text-muted-foreground mt-2">Preparing your results...</p>
          </div>
        )}
      </div>
    </div>
  )
}
