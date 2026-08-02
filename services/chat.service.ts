import { requireUserId } from '@/lib/auth-helpers';
import { CHAT_HISTORY_COLUMNS } from '@/lib/supabase-live-schema';
import { supabase } from '@/lib/supabase';
import {
  generateChatResponse,
  getApplicationContext,
} from '@/services/analysis.service';
import type { ChatHistoryInsert, ChatHistoryMessage } from '@/types/chat';

const WELCOME_MESSAGE =
  'Hello! I am your ApplyWise AI assistant. I can help you with your application process. Ask me anything about your documents, timeline, or recommendations.';

export const ChatService = {
  async getMessages(applicationId: string): Promise<ChatHistoryMessage[]> {
    await requireUserId();

    const { data, error } = await supabase
      .from('chat_history')
      .select(CHAT_HISTORY_COLUMNS)
      .eq('application_id', applicationId)
      .order('created_at', { ascending: true });

    if (error) throw new Error(error.message);
    return (data ?? []) as ChatHistoryMessage[];
  },

  async ensureWelcomeMessage(applicationId: string): Promise<ChatHistoryMessage[]> {
    const existing = await this.getMessages(applicationId);
    if (existing.length > 0) return existing;

    await this.insertMessage({
      application_id: applicationId,
      role: 'assistant',
      message: WELCOME_MESSAGE,
    });

    return this.getMessages(applicationId);
  },

  async insertMessage(payload: ChatHistoryInsert): Promise<ChatHistoryMessage> {
    await requireUserId();

    const { data, error } = await supabase
      .from('chat_history')
      .insert({
        application_id: payload.application_id,
        role: payload.role,
        message: payload.message,
        created_at: payload.created_at ?? new Date().toISOString(),
      })
      .select(CHAT_HISTORY_COLUMNS)
      .single();

    if (error) throw new Error(error.message);
    return data as ChatHistoryMessage;
  },

  async sendMessage(
    applicationId: string,
    content: string,
  ): Promise<{ userMessage: ChatHistoryMessage; assistantMessage: ChatHistoryMessage }> {
    const userMessage = await this.insertMessage({
      application_id: applicationId,
      role: 'user',
      message: content,
    });

    const context = await getApplicationContext(applicationId);
    const responseContent = generateChatResponse(content, context);

    const assistantMessage = await this.insertMessage({
      application_id: applicationId,
      role: 'assistant',
      message: responseContent,
    });

    return { userMessage, assistantMessage };
  },
};
