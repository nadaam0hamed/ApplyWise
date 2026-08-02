// OCR Agent Service
// This is a mock service that will be replaced with LangChain/OpenAI integration

import { AgentLog } from '../types'

interface OCRResult {
  logs: AgentLog[]
  extractedText: string[]
}

export async function ocrService(): Promise<OCRResult> {
  const logs: AgentLog[] = []
  const extractedText: string[] = []

  const mockExtractions = [
    'Extracting text from Passport.pdf',
    'Extracting text from Academic_Transcript.pdf',
    'Extracting text from CV.pdf',
    'Extracting text from IELTS_Score.pdf',
  ]

  for (const extraction of mockExtractions) {
    await new Promise(resolve => setTimeout(resolve, 250))

    logs.push({
      id: `log-${Date.now()}-${Math.random()}`,
      timestamp: new Date(),
      message: extraction,
      type: 'info',
    })

    extractedText.push(`Text from ${extraction}`)
  }

  logs.push({
    id: `log-${Date.now()}-${Math.random()}`,
    timestamp: new Date(),
    message: 'OCR extraction completed',
    type: 'success',
  })

  return { logs, extractedText }
}
