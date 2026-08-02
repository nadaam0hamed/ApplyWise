'use client';

import { MessageSquare } from 'lucide-react';

import { ChatPanel } from '@/components/chat/ChatPanel';
import { useApplicationChat } from '@/hooks/useApplicationChat';

type ApplicationChatSectionProps = {
  applicationId: string;
};

export function ApplicationChatSection({ applicationId }: ApplicationChatSectionProps) {
  const { messages, isLoading, isSending, error, sendMessage, retry } =
    useApplicationChat(applicationId);

  return (
    <section className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-foreground flex items-center gap-2">
          <MessageSquare size={24} className="text-secondary" />
          AI Chat
        </h2>
        <p className="text-sm text-muted-foreground mt-1">
          Ask questions about your documents, analysis results, and application requirements
        </p>
      </div>

      <ChatPanel
        messages={messages}
        isLoading={isLoading}
        isSending={isSending}
        error={error}
        onSendMessage={sendMessage}
        onRetry={retry}
      />
    </section>
  );
}
