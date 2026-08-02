// Information Extraction Agent Service
// This is a mock service that will be replaced with OpenAI structured outputs

import { AgentLog } from '../types'

interface ExtractionResult {
  logs: AgentLog[]
  extractedData: Record<string, string>
}

export async function informationExtractionService(): Promise<ExtractionResult> {
  const logs: AgentLog[] = []
  const extractedData: Record<string, string> = {}

  const fields = [
    { field: 'Full Name', value: 'John Doe' },
    { field: 'Email', value: 'john.doe@example.com' },
    { field: 'Nationality', value: 'United States' },
    { field: 'Target University', value: 'Stanford University' },
    { field: 'Target Program', value: 'MS Computer Science' },
    { field: 'Academic Score (GPA)', value: '3.85' },
  ]

  for (const { field, value } of fields) {
    await new Promise(resolve => setTimeout(resolve, 200))

    logs.push({
      id: `log-${Date.now()}-${Math.random()}`,
      timestamp: new Date(),
      message: `Extracting: ${field}`,
      type: 'info',
    })

    extractedData[field] = value
  }

  logs.push({
    id: `log-${Date.now()}-${Math.random()}`,
    timestamp: new Date(),
    message: 'Information extraction completed',
    type: 'success',
  })

  return { logs, extractedData }
}
