'use client';

import { useEffect, useRef, useState } from 'react';
import { AlertCircle, Loader2, Send, RefreshCw } from 'lucide-react';

import type { ChatResponseMessage } from '@/types/chat';

type ChatPanelProps = {
  messages: ChatResponseMessage[];
  isLoading?: boolean;
  isSending?: boolean;
  error?: string | null;
  onSendMessage: (message: string) => Promise<void>;
  onRetry?: () => void;
  suggestedPrompts?: string[];
};

export function ChatPanel({
  messages,
  isLoading = false,
  isSending = false,
  error = null,
  onSendMessage,
  onRetry,
  suggestedPrompts = [
    'What documents do I still need?',
    'Help me write my Statement of Purpose',
    'When is my application deadline?',
    'What is my current readiness score?',
  ],
}: ChatPanelProps) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isSending]);

  const handleSendMessage = async (text: string = input) => {
    if (!text.trim() || isSending) return;

    setInput('');
    try {
      await onSendMessage(text);
    } catch {
      setInput(text);
    }
  };

  const showSuggestedPrompts =
    !isLoading && !error && messages.length <= 1 && suggestedPrompts.length > 0;

  return (
    <div className="flex flex-col gap-4">
      {error && (
        <div className="premium-card p-4 border border-red-500/30 bg-red-500/10 flex items-start gap-3">
          <AlertCircle size={20} className="text-red-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="font-medium text-foreground">Chat error</p>
            <p className="text-sm text-muted-foreground mt-1">{error}</p>
            {onRetry && (
              <button
                onClick={onRetry}
                className="mt-2 text-sm text-secondary hover:underline flex items-center gap-1"
              >
                <RefreshCw size={14} />
                Retry
              </button>
            )}
          </div>
        </div>
      )}

      <div className="premium-card p-4 flex flex-col min-h-[320px] max-h-[480px]">
        <div className="flex-1 overflow-y-auto space-y-4 pr-1 mb-4">
          {isLoading ? (
            <div className="flex items-center justify-center gap-3 py-12">
              <Loader2 size={24} className="animate-spin text-secondary" />
              <span className="text-muted-foreground">Loading chat…</span>
            </div>
          ) : (
            <>
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-xl rounded-lg px-4 py-3 ${
                      message.type === 'user'
                        ? 'bg-gradient-to-r from-primary to-secondary text-background'
                        : 'glassmorphism text-foreground border border-secondary/20'
                    }`}
                  >
                    <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
                    <p
                      className={`text-xs mt-1 ${
                        message.type === 'user' ? 'text-background/70' : 'text-muted-foreground'
                      }`}
                    >
                      {new Date(message.timestamp).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </p>
                  </div>
                </div>
              ))}

              {isSending && (
                <div className="flex justify-start">
                  <div className="glassmorphism rounded-lg px-4 py-3 border border-secondary/20">
                    <div className="flex gap-2">
                      <div className="w-2 h-2 rounded-full bg-secondary animate-bounce" />
                      <div
                        className="w-2 h-2 rounded-full bg-secondary animate-bounce"
                        style={{ animationDelay: '0.1s' }}
                      />
                      <div
                        className="w-2 h-2 rounded-full bg-secondary animate-bounce"
                        style={{ animationDelay: '0.2s' }}
                      />
                    </div>
                  </div>
                </div>
              )}
            </>
          )}

          <div ref={messagesEndRef} />
        </div>

        {showSuggestedPrompts && (
          <div className="mb-4 space-y-3">
            <p className="text-sm text-muted-foreground">Try asking:</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {suggestedPrompts.map((prompt) => (
                <button
                  key={prompt}
                  type="button"
                  onClick={() => handleSendMessage(prompt)}
                  disabled={isSending}
                  className="p-3 rounded-lg border border-secondary/30 text-foreground hover:bg-secondary/10 hover:border-secondary/50 transition text-left text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="glassmorphism rounded-xl p-4 border border-secondary/20">
          <div className="flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && !event.shiftKey) {
                  event.preventDefault();
                  handleSendMessage();
                }
              }}
              placeholder="Ask about your documents, requirements, or recommendations…"
              disabled={isLoading || isSending}
              className="flex-1 bg-input border border-border rounded-lg px-4 py-2 text-foreground placeholder-muted-foreground focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition disabled:opacity-50"
            />
            <button
              type="button"
              onClick={() => handleSendMessage()}
              disabled={!input.trim() || isLoading || isSending}
              className="p-2 rounded-lg bg-gradient-to-r from-primary to-secondary text-background hover:shadow-lg hover:shadow-primary/20 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send size={20} />
            </button>
          </div>
          <p className="text-xs text-muted-foreground mt-2">Press Enter to send</p>
        </div>
      </div>
    </div>
  );
}
