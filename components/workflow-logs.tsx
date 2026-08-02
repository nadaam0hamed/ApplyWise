'use client'

import { useEffect, useRef } from 'react'
import { WorkflowLog } from '@/lib/ai-agents/types'

interface WorkflowLogsProps {
  logs: WorkflowLog[]
  maxHeight?: string
}

export function WorkflowLogs({ logs, maxHeight = 'max-h-80' }: WorkflowLogsProps) {
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // Auto-scroll to bottom when new logs arrive
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [logs])

  const getLogColor = (type: string) => {
    switch (type) {
      case 'success':
        return 'text-secondary'
      case 'error':
        return 'text-destructive'
      case 'warning':
        return 'text-yellow-400'
      default:
        return 'text-muted-foreground'
    }
  }

  const getLogIcon = (type: string) => {
    switch (type) {
      case 'success':
        return '✓'
      case 'error':
        return '✗'
      case 'warning':
        return '⚠'
      default:
        return '→'
    }
  }

  return (
    <div
      ref={scrollRef}
      className={`${maxHeight} overflow-y-auto rounded-lg border border-border bg-muted/5 p-4 font-mono text-sm space-y-1`}
    >
      {logs.length === 0 ? (
        <div className="text-muted-foreground">Waiting for logs...</div>
      ) : (
        logs.map((log) => (
          <div key={log.id} className="flex gap-2 animate-in fade-in duration-200">
            <span className={`flex-shrink-0 ${getLogColor(log.type)}`}>{getLogIcon(log.type)}</span>
            <span className="text-muted-foreground">[{log.timestamp.toLocaleTimeString()}]</span>
            <span className={getLogColor(log.type)}>{log.message}</span>
          </div>
        ))
      )}
    </div>
  )
}
