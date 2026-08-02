# AI Multi-Agent Workflow Platform

This directory contains the architecture for a professional AI workflow platform with a multi-agent AI pipeline system. The architecture is designed to be framework-agnostic and easily extensible with real AI/ML backends.

## Architecture Overview

```
User Upload
    ↓
[Multi-Agent Pipeline]
    ├── Document Reader Agent (reads uploaded files)
    ├── OCR Agent (extracts text from images)
    ├── Information Extraction Agent (extracts applicant info)
    ├── Requirement Checker Agent (validates documents)
    ├── Knowledge Retrieval Agent (RAG - vector DB)
    ├── Checklist Generator Agent (creates personalized checklist)
    ├── Timeline Planner Agent (generates timeline)
    ├── Recommendation Agent (improvement suggestions)
    ├── AI Report Generator (creates final report)
    └── AI Assistant (ready for questions)
    ↓
Analysis Results Display
```

## Directory Structure

```
lib/ai-agents/
├── types.ts                 # TypeScript types and interfaces
├── agents.ts               # Agent definitions and metadata
├── README.md               # This file
└── services/
    ├── workflow-orchestrator.ts    # Main orchestrator
    ├── document-reader.ts          # Document reading service
    ├── ocr.ts                      # OCR extraction service
    ├── information-extraction.ts   # Data extraction service
    ├── requirement-checker.ts      # Validation service
    └── knowledge-retrieval.ts      # RAG service
```

## Components

```
components/
├── multi-agent-pipeline.tsx    # Main UI for agent execution
├── agent-activity-panel.tsx    # Displays agent status/logs
└── workflow-logs.tsx           # Logs display component
```

## Service Architecture

### Core Types (`types.ts`)

- **AgentState**: `'waiting' | 'running' | 'completed' | 'error'`
- **AIAgent**: Agent definition with metadata
- **AgentActivity**: Real-time agent execution status
- **WorkflowLog**: Log entries with timestamps and types
- **AnalysisResult**: Final analysis output

### Agent Definitions (`agents.ts`)

10 agents that run sequentially:

1. **Document Reader Agent** - Reads uploaded files
2. **OCR Agent** - Extracts text from images
3. **Information Extraction Agent** - Parses applicant information
4. **Requirement Checker Agent** - Validates against requirements
5. **Knowledge Retrieval Agent** - Retrieves relevant information (RAG)
6. **Checklist Generator Agent** - Creates personalized checklist
7. **Timeline Planner Agent** - Generates submission timeline
8. **Recommendation Agent** - Suggests improvements
9. **AI Report Generator** - Creates final analysis report
10. **AI Assistant** - Ready for follow-up questions

### Workflow Orchestrator (`workflow-orchestrator.ts`)

Coordinates agent execution in sequence:

```typescript
// Execute the complete workflow
const result = await executeWorkflow()
const { activities, allLogs } = result

// Access individual agent status
activities.get('document-reader').state // 'completed' | 'running' | 'waiting' | 'error'
activities.get('ocr').logs              // Agent-specific logs
```

### Service Pattern

Each agent has a dedicated service file that:

1. Takes input from the previous agent (or user)
2. Simulates the processing with realistic delays
3. Returns logs and results
4. Can be easily replaced with real AI/ML implementations

Example service pattern:

```typescript
export async function documentReaderService(): Promise<DocumentReaderResult> {
  const logs: AgentLog[] = []
  
  // Simulate processing
  logs.push({
    id: generateId(),
    timestamp: new Date(),
    message: 'Reading Passport.pdf',
    type: 'info',
  })
  
  return { logs, documents }
}
```

## Integration Guide

### Replace with Real LangChain/LangGraph

Update `workflow-orchestrator.ts`:

```typescript
import { initializeAgentExecutor } from 'langchain/agents'
import { OpenAI } from 'langchain/llms/openai'

export async function executeWorkflow() {
  const model = new OpenAI({ apiKey: process.env.OPENAI_API_KEY })
  const executor = await initializeAgentExecutor(
    [documentReaderTool, ocrTool, ...],
    model
  )
  
  const result = await executor.invoke({
    input: 'Process uploaded documents',
  })
  
  return result
}
```

### Replace with Real LLM Services

Update individual services:

```typescript
// services/information-extraction.ts
import { OpenAI } from 'openai'
import { parser } from 'openai-structured-outputs'

export async function informationExtractionService(documents: string[]) {
  const client = new OpenAI()
  
  const response = await client.beta.chat.completions.create({
    model: 'gpt-4o',
    messages: [{ role: 'user', content: `Extract data from: ${documents}` }],
    response_format: {
      type: 'json_schema',
      json_schema: {
        name: 'ApplicantData',
        schema: ApplicantDataSchema,
      },
    },
  })
  
  return parser.parse(response)
}
```

### Add Vector Database (RAG)

Replace `knowledge-retrieval.ts`:

```typescript
import { Chroma } from 'langchain/vectorstores/chroma'
import { OpenAIEmbeddings } from 'langchain/embeddings/openai'

export async function knowledgeRetrievalService(query: string) {
  const embeddings = new OpenAIEmbeddings()
  const vectorStore = new Chroma({ embeddings })
  
  const results = await vectorStore.similaritySearch(query, 5)
  return results
}
```

## UI Components

### MultiAgentPipeline

Main component showing:
- Overall progress bar
- Agent activity panel with real-time updates
- Workflow logs (auto-scrolling)
- Pipeline visualization
- Completion status

### AgentActivityPanel

Displays each agent with:
- Current state (waiting/running/completed/error)
- State-specific styling and icons
- Last 3 logs from each agent
- Progress bars for running agents
- Error messages if applicable

### WorkflowLogs

Professional log display with:
- Auto-scrolling to latest
- Color-coded log types
- Timestamps
- Fade-in animations

## State Management

Agent states and their visual representation:

| State | Style | Icon | Animation |
|-------|-------|------|-----------|
| **waiting** | Gray | Gray circle | None |
| **running** | Blue | Spinning loader | Pulse + Glow |
| **completed** | Green | Check mark | None |
| **error** | Red | Alert icon | None |

## Example Usage

```typescript
// In a React component
const { activities, allLogs } = await executeWorkflow()

// Check if a specific agent is complete
if (activities.get('document-reader').state === 'completed') {
  // Process next step
}

// Access all logs
console.log(allLogs.map(log => `[${log.timestamp}] ${log.message}`))
```

## Environment Variables (For Future Implementation)

```bash
# OpenAI
OPENAI_API_KEY=sk_...

# Vector Database
CHROMA_HOST=localhost
CHROMA_PORT=8000

# LangChain
LANGCHAIN_API_KEY=ls_...

# FastAPI Backend
FASTAPI_URL=http://localhost:8000
```

## Performance Considerations

- Agents run sequentially by default
- Can be parallelized with LangGraph for independent tasks
- Mock services have realistic delays (200-400ms per action)
- Real implementations should measure actual processing time
- Logs are streamed in real-time to UI

## Testing

Each service is independently testable:

```typescript
import { documentReaderService } from '@/lib/ai-agents/services/document-reader'

test('document reader service', async () => {
  const result = await documentReaderService()
  expect(result.logs.length).toBeGreaterThan(0)
  expect(result.documents.length).toBeGreaterThan(0)
})
```

## Future Enhancements

- [ ] Parallel agent execution with LangGraph
- [ ] Agent retries and error recovery
- [ ] Webhook notifications for long-running tasks
- [ ] Agent performance metrics and monitoring
- [ ] Custom agent creation framework
- [ ] Agent memory/context persistence
- [ ] Multi-language support
- [ ] A/B testing different agent chains

## API Design (For Backend Integration)

```typescript
POST /api/workflow/execute
{
  "documentIds": ["doc-1", "doc-2"],
  "userId": "user-123"
}

Response:
{
  "workflowId": "wf-456",
  "agents": [
    {
      "id": "document-reader",
      "state": "completed",
      "logs": [...]
    },
    ...
  ],
  "overall_progress": 30
}
```

WebSocket for real-time updates:

```typescript
ws://api.example.com/ws/workflow/wf-456

Message:
{
  "agentId": "ocr",
  "state": "running",
  "logs": [...],
  "timestamp": "2024-07-25T10:30:00Z"
}
```
