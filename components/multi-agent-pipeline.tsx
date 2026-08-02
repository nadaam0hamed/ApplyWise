'use client'

import { useState, useEffect } from 'react'
import { AgentActivity } from '@/lib/ai-agents/types'
import { AI_AGENTS } from '@/lib/ai-agents/agents'
import { AgentActivityPanel } from './agent-activity-panel'
import { WorkflowLogs } from './workflow-logs'
import { executeWorkflow } from '@/lib/ai-agents/services/workflow-orchestrator'
import { CheckCircle2 } from 'lucide-react'

interface MultiAgentPipelineProps {
  onComplete: () => void
}

export function MultiAgentPipeline({ onComplete }: MultiAgentPipelineProps) {
  const [activities, setActivities] = useState<Map<string, AgentActivity>>(new Map())
  const [logs, setLogs] = useState<any[]>([])
  const [isComplete, setIsComplete] = useState(false)
  const [overallProgress, setOverallProgress] = useState(0)

  useEffect(() => {
    let isMounted = true

    const runWorkflow = async () => {
      try {
        const result = await executeWorkflow()

        if (isMounted) {
          // Update activities as they complete
          const activitiesMap = new Map(result.activities)
          setActivities(activitiesMap)
          setLogs(result.allLogs)

          // Calculate progress
          const completed = Array.from(activitiesMap.values()).filter(
            (a) => a.state === 'completed'
          ).length
          const total = activitiesMap.size
          setOverallProgress((completed / total) * 100)

          // Check if all completed
          if (completed === total) {
            setIsComplete(true)
            // Delay final transition
            setTimeout(() => {
              if (isMounted) {
                onComplete()
              }
            }, 1500)
          }
        }
      } catch (error) {
        console.error('Workflow error:', error)
      }
    }

    runWorkflow()

    return () => {
      isMounted = false
    }
  }, [onComplete])

  // Sort agents by order
  const sortedAgents = Array.from(activities.entries())
    .sort(([, a], [, b]) => {
      const agentA = AI_AGENTS.find((agent) => agent.id === a.agentId)
      const agentB = AI_AGENTS.find((agent) => agent.id === b.agentId)
      return (agentA?.order || 0) - (agentB?.order || 0)
    })

  return (
    <div className="min-h-screen bg-gradient-to-b from-background via-background to-background py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-5xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center space-y-3">
          <h1 className="text-4xl font-bold text-foreground">AI Workflow Processing</h1>
          <p className="text-muted-foreground">Multi-Agent AI Pipeline in Action</p>
        </div>

        {/* Overall Progress */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-muted-foreground">Overall Progress</span>
            <span className="text-sm font-bold text-secondary">{Math.round(overallProgress)}%</span>
          </div>
          <div className="h-2 bg-secondary/20 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-primary to-secondary transition-all duration-500 shadow-lg shadow-secondary/40"
              style={{ width: `${overallProgress}%` }}
            />
          </div>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Agent Activity Panel - Main View */}
          <div className="lg:col-span-2">
            <div className="glassmorphism rounded-xl p-6 border border-secondary/20">
              <h2 className="text-lg font-semibold text-foreground mb-4">Agent Activity</h2>
              <AgentActivityPanel activities={activities} />
            </div>
          </div>

          {/* Workflow Logs - Sidebar */}
          <div className="lg:col-span-1">
            <div className="glassmorphism rounded-xl p-4 border border-secondary/20 h-full">
              <h3 className="text-sm font-semibold text-foreground mb-4">Workflow Logs</h3>
              <WorkflowLogs logs={logs} maxHeight="max-h-96" />
            </div>
          </div>
        </div>

        {/* Agent Pipeline Visualization */}
        <div className="glassmorphism rounded-xl p-6 border border-secondary/20">
          <h2 className="text-lg font-semibold text-foreground mb-6">Pipeline Workflow</h2>
          <div className="space-y-3">
            {sortedAgents.map(([agentId, activity], idx) => {
              const agent = AI_AGENTS.find((a) => a.id === agentId)
              if (!agent) return null

              const isCompleted = activity.state === 'completed'
              const isRunning = activity.state === 'running'

              return (
                <div key={agentId}>
                  <div className="flex items-center gap-4">
                    {/* Index */}
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold transition-all ${
                        isCompleted
                          ? 'bg-secondary/20 text-secondary'
                          : isRunning
                            ? 'bg-primary/20 text-primary'
                            : 'bg-muted/20 text-muted-foreground'
                      }`}
                    >
                      {isCompleted ? '✓' : agent.order}
                    </div>

                    {/* Agent Info */}
                    <div className="flex-1">
                      <p className="text-sm font-medium text-foreground">{agent.name}</p>
                      <p className="text-xs text-muted-foreground">{agent.description}</p>
                    </div>

                    {/* Status Badge */}
                    <div
                      className={`text-xs font-semibold px-3 py-1 rounded-full ${
                        isCompleted
                          ? 'bg-secondary/20 text-secondary'
                          : isRunning
                            ? 'bg-primary/20 text-primary flex items-center gap-1.5'
                            : 'bg-muted/20 text-muted-foreground'
                      }`}
                    >
                      {isRunning && <div className="w-1.5 h-1.5 bg-primary rounded-full animate-pulse" />}
                      {isCompleted ? 'Done' : isRunning ? 'Running' : 'Waiting'}
                    </div>
                  </div>

                  {/* Connecting Line */}
                  {idx < sortedAgents.length - 1 && (
                    <div className="ml-4 mt-3 h-6 border-l border-secondary/30 border-dashed" />
                  )}
                </div>
              )
            })}
          </div>
        </div>

        {/* Completion State */}
        {isComplete && (
          <div className="text-center space-y-4 animate-in fade-in duration-500">
            <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-secondary/20 border-2 border-secondary shadow-lg shadow-secondary/20">
              <CheckCircle2 className="w-10 h-10 text-secondary" />
            </div>
            <div>
              <h3 className="text-2xl font-bold text-foreground">✓ All AI Agents Completed Successfully</h3>
              <p className="text-muted-foreground mt-2">Generating final analysis results...</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
