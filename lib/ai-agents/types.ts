// Agent States
export type AgentState = 'waiting' | 'running' | 'completed' | 'error'

// Agent Log Entry
export interface AgentLog {
  id: string
  timestamp: Date
  message: string
  type: 'info' | 'success' | 'error' | 'warning'
}

// AI Agent Definition
export interface AIAgent {
  id: string
  name: string
  description: string
  icon: string
  order: number
}

// Agent Activity (real-time status)
export interface AgentActivity {
  agentId: string
  state: AgentState
  progress: number
  logs: AgentLog[]
  startTime?: Date
  endTime?: Date
  error?: string
}

// Workflow Log Entry (for display)
export interface WorkflowLog {
  id: string
  timestamp: Date
  agentId: string
  message: string
  type: 'info' | 'success' | 'error' | 'warning'
}

// Analysis Result
export interface AnalysisResult {
  applicantInfo: {
    name: string
    email: string
    phone: string
    targetProgram: string
    targetUniversity: string
  }
  uploadedDocuments: Array<{ name: string; status: string; date: string }>
  missingDocuments: Array<{ name: string; priority: string }>
  checklist: Array<{ item: string; completed: boolean }>
  timeline: Array<{ date: string; event: string }>
  readinessScore: number
  recommendations: string[]
}
