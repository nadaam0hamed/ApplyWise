// Document Reader Agent Service
// This is a mock service that will be replaced with LangChain integration

import { AgentLog } from '../types'

interface DocumentReaderResult {
  logs: AgentLog[]
  documents: string[]
}

export async function documentReaderService(): Promise<DocumentReaderResult> {
  const logs: AgentLog[] = []
  const documents: string[] = []

  // Simulate reading documents
  const mockDocuments = [
    'Reading Passport.pdf',
    'Reading Academic_Transcript.pdf',
    'Reading CV.pdf',
    'Reading IELTS_Score.pdf',
  ]

  for (const doc of mockDocuments) {
    // Add simulated delay
    await new Promise(resolve => setTimeout(resolve, 300))

    logs.push({
      id: `log-${Date.now()}-${Math.random()}`,
      timestamp: new Date(),
      message: doc,
      type: 'info',
    })

    documents.push(doc)
  }

  logs.push({
    id: `log-${Date.now()}-${Math.random()}`,
    timestamp: new Date(),
    message: 'Document reading completed',
    type: 'success',
  })

  return { logs, documents }
}
