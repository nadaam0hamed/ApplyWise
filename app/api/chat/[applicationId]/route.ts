import { NextRequest, NextResponse } from 'next/server';

import { handleChatMessage, listChatMessages } from '@/lib/chat-server';
import { createServerSupabaseClient } from '@/lib/serverSupabase';

export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

type RouteContext = {
  params: Promise<{ applicationId: string }>;
};

type ChatErrorResponse = {
  error?: string;
  detail?: string | string[];
};

function getErrorMessage(error: ChatErrorResponse): string {
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
  return error.error || 'Chat request failed';
}

/** Application-scoped AI chat. */
export async function GET(_request: NextRequest, context: RouteContext) {
  try {
    const { applicationId } = await context.params;
    const supabase = await createServerSupabaseClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();

    if (!user) {
      return NextResponse.json({ error: 'You must be logged in to access chat' }, { status: 401 });
    }

    const messages = await listChatMessages(supabase, user.id, applicationId);
    return NextResponse.json({ success: true, messages });
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Failed to load chat';
    return NextResponse.json(
      { error: errorMessage },
      { status: 500 },
    );
  }
}

export async function POST(request: NextRequest, context: RouteContext) {
  try {
    const { applicationId } = await context.params;
    const supabase = await createServerSupabaseClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();

    if (!user) {
      return NextResponse.json({ error: 'You must be logged in to send messages' }, { status: 401 });
    }

    const body = await request.json();
    const { message } = body;

    if (!message || typeof message !== 'string') {
      return NextResponse.json({ error: 'Message is required and must be a string' }, { status: 400 });
    }

    if (!message.trim()) {
      return NextResponse.json({ error: 'Message cannot be empty' }, { status: 400 });
    }

    const { userMessage, assistantMessage } = await handleChatMessage(
      supabase,
      user.id,
      message,
      applicationId,
    );

    return NextResponse.json({
      success: true,
      messages: [userMessage, assistantMessage],
      message: assistantMessage,
    });
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Chat request failed';
    return NextResponse.json(
      { error: errorMessage },
      { status: 500 },
    );
  }
}
