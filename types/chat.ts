/**
 * Maps to the live `chat_history` Supabase table.
 * Columns: id, application_id, role, message, created_at
 */

export type ChatMessageRole = 'user' | 'assistant' | 'system';

/** Row in the live `chat_history` table. */
export interface ChatHistoryMessage {
  id: string;
  application_id: string;
  role: ChatMessageRole;
  message: string;
  created_at: string;
}

/** Payload for inserting a chat history row. */
export interface ChatHistoryInsert {
  application_id: string;
  role: ChatMessageRole;
  message: string;
  created_at?: string;
}

/** Message shape used by the chat UI. */
export interface ChatResponseMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: string;
}
