'use client';

import { useCallback, useEffect, useState } from 'react';

import type { ChatResponseMessage } from '@/types/chat';

type ChatApiResponse = {
  success?: boolean;
  messages?: ChatResponseMessage[];
  message?: ChatResponseMessage;
  error?: string;
  detail?: string | string[];
};

function getErrorMessage(error: ChatApiResponse): string {
  if (error.detail) {
    if (Array.isArray(error.detail)) {
      return error.detail.map((d) => {
        if (typeof d === 'string') return d;
        if (typeof d === 'object' && d !== null && 'msg' in d) {
          return String((d as { msg?: string }).msg);
        }
        return 'Unknown error';
      }).join(', ');
    }
    return error.detail;
  }
  return error.error || 'An unexpected error occurred';
}

export function useApplicationChat(applicationId: string) {
  const [messages, setMessages] = useState<ChatResponseMessage[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadMessages = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/chat/${applicationId}`);
      const data = (await response.json()) as ChatApiResponse;

      if (!response.ok) {
        const errorMessage = getErrorMessage(data);
        switch (response.status) {
          case 400:
            throw new Error(`Invalid request: ${errorMessage}`);
          case 401:
            throw new Error('You must be logged in to access chat');
          case 404:
            throw new Error('Application not found. Please select a valid application.');
          case 500:
            throw new Error(`Server error: ${errorMessage}`);
          default:
            throw new Error(errorMessage);
        }
      }

      setMessages(data.messages ?? []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load chat');
      setMessages([]);
    } finally {
      setIsLoading(false);
    }
  }, [applicationId]);

  useEffect(() => {
    loadMessages();
  }, [loadMessages]);

  const sendMessage = useCallback(
    async (content: string) => {
      const trimmed = content.trim();
      if (!trimmed || isSending) return;

      setIsSending(true);
      setError(null);

      try {
        const response = await fetch(`/api/chat/${applicationId}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: trimmed }),
        });
        const data = (await response.json()) as ChatApiResponse;

        if (!response.ok) {
          const errorMessage = getErrorMessage(data);
          switch (response.status) {
            case 400:
              throw new Error(`Invalid request: ${errorMessage}`);
            case 401:
              throw new Error('You must be logged in to send messages');
            case 404:
              throw new Error('Application not found. Please select a valid application.');
            case 422:
              throw new Error(`Invalid message format: ${errorMessage}`);
            case 500:
              throw new Error(`Server error: ${errorMessage}`);
            default:
              throw new Error(errorMessage);
          }
        }

        if (data.messages?.length) {
          setMessages((prev) => [...prev, ...data.messages!]);
        } else if (data.message) {
          setMessages((prev) => [...prev, data.message!]);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to send message');
        throw err;
      } finally {
        setIsSending(false);
      }
    },
    [applicationId, isSending],
  );

  const retry = useCallback(() => {
    setError(null);
    loadMessages();
  }, [loadMessages]);

  return {
    messages,
    isLoading,
    isSending,
    error,
    sendMessage,
    refresh: loadMessages,
    retry,
  };
}
