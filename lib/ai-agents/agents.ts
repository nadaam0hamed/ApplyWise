import { AIAgent } from './types'

export const AI_AGENTS: AIAgent[] = [
  {
    id: 'document-reader',
    name: 'Document Reader Agent',
    description: 'Reads uploaded files',
    icon: '📄',
    order: 1,
  },
  {
    id: 'ocr',
    name: 'OCR Agent',
    description: 'Extracts text from images',
    icon: '🔍',
    order: 2,
  },
  {
    id: 'information-extraction',
    name: 'Information Extraction Agent',
    description: 'Extracts applicant information',
    icon: '🧠',
    order: 3,
  },
  {
    id: 'requirement-checker',
    name: 'Requirement Checker Agent',
    description: 'Compares documents with official requirements',
    icon: '✓',
    order: 4,
  },
  {
    id: 'knowledge-retrieval',
    name: 'Knowledge Retrieval Agent (RAG)',
    description: 'Retrieves relevant scholarship, university and visa information',
    icon: '📚',
    order: 5,
  },
  {
    id: 'checklist-generator',
    name: 'Checklist Generator Agent',
    description: 'Builds personalized checklist',
    icon: '📋',
    order: 6,
  },
  {
    id: 'timeline-planner',
    name: 'Timeline Planner Agent',
    description: 'Creates submission timeline',
    icon: '📅',
    order: 7,
  },
  {
    id: 'recommendation',
    name: 'Recommendation Agent',
    description: 'Generates improvement suggestions',
    icon: '💡',
    order: 8,
  },
  {
    id: 'report-generator',
    name: 'AI Report Generator',
    description: 'Creates final report',
    icon: '📊',
    order: 9,
  },
  {
    id: 'ai-assistant',
    name: 'AI Assistant',
    description: 'Ready for questions',
    icon: '🤖',
    order: 10,
  },
]
