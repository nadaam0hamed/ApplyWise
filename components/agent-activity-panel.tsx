'use client'

import { AgentActivity } from '@/lib/ai-agents/types'
import { AI_AGENTS } from '@/lib/ai-agents/agents'
import { CheckCircle2, AlertCircle, Loader2 } from 'lucide-react'

interface AgentActivityPanelProps {
  activities: Map<string, AgentActivity>
}

export function AgentActivityPanel({ activities }: AgentActivityPanelProps) {
  const getAgentInfo = (agentId: string) => {
    return AI_AGENTS.find(agent => agent.id === agentId)
  }

  const getStateStyles = (state: string) => {
    switch (state) {
      case 'completed':
        return {
          bg: 'bg-secondary/10',
          border: 'border-secondary/40',
          icon: 'text-secondary',
          text: 'text-foreground',
        }
      case 'running':
        return {
          bg: 'bg-primary/10',
          border: 'border-primary/40',
          icon: 'text-primary',
          text: 'text-foreground',
        }
      case 'error':
        return {
          bg: 'bg-destructive/10',
          border: 'border-destructive/40',
          icon: 'text-destructive',
          text: 'text-foreground',
        }
      default: // waiting
        return {
          bg: 'bg-muted/5',
          border: 'border-muted/20',
          icon: 'text-muted-foreground',
          text: 'text-muted-foreground',
        }
    }
  }

  const getStateIcon = (state: string) => {
    switch (state) {
      case 'completed':
        return <CheckCircle2 className="w-5 h-5 text-secondary" />
      case 'running':
        return <Loader2 className="w-5 h-5 text-primary animate-spin" />
      case 'error':
        return <AlertCircle className="w-5 h-5 text-destructive" />
      default: // waiting
        return <div className="w-5 h-5 rounded-full bg-muted-foreground/30" />
    }
  }

  const sortedAgents = Array.from(activities.entries())
    .sort(([, a], [, b]) => {
      const agentA = getAgentInfo(a.agentId)
      const agentB = getAgentInfo(b.agentId)
      return (agentA?.order || 0) - (agentB?.order || 0)
    })

  return (
    <div className="space-y-3">
      {sortedAgents.map(([agentId, activity]) => {
        const agent = getAgentInfo(agentId)
        const styles = getStateStyles(activity.state)

        if (!agent) return null

        return (
          <div
            key={agentId}
            className={`transition-all duration-300 rounded-lg border p-4 ${styles.bg} ${styles.border} ${
              activity.state === 'running' ? 'ring-1 ring-primary/20 animate-agent-glow' : ''
            } animate-slide-in-top`}
          >
            <div className="flex items-start gap-3">
              <div className="pt-0.5">{getStateIcon(activity.state)}</div>

              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className={`font-semibold text-sm ${styles.text}`}>{agent.name}</p>
                    <p className="text-xs text-muted-foreground mt-1">{agent.description}</p>
                  </div>
                  <span
                    className={`text-xs font-medium px-2 py-1 rounded-full whitespace-nowrap ${
                      activity.state === 'completed'
                        ? 'bg-secondary/20 text-secondary'
                        : activity.state === 'running'
                          ? 'bg-primary/20 text-primary'
                          : activity.state === 'error'
                            ? 'bg-destructive/20 text-destructive'
                            : 'bg-muted/20 text-muted-foreground'
                    }`}
                  >
                    {activity.state.charAt(0).toUpperCase() + activity.state.slice(1)}
                  </span>
                </div>

                {/* Progress bar for running state */}
                {activity.state === 'running' && (
                  <div className="mt-3 h-1 bg-muted rounded-full overflow-hidden">
                    <div className="h-full bg-gradient-to-r from-primary to-secondary animate-pulse" />
                  </div>
                )}

                {/* Logs display */}
                {activity.logs.length > 0 && (
                  <div className="mt-3 space-y-1 text-xs">
                    {activity.logs.slice(-3).map((log, idx) => (
                      <div key={idx} className="text-muted-foreground flex gap-2">
                        <span className="flex-shrink-0">
                          {log.type === 'success' ? '✓' : log.type === 'error' ? '✗' : log.type === 'warning' ? '⚠' : '→'}
                        </span>
                        <span className="line-clamp-1">{log.message}</span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Error message */}
                {activity.error && <p className="text-xs text-destructive mt-2">{activity.error}</p>}
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
