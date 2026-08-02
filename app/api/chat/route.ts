import { NextRequest, NextResponse } from 'next/server';

import { handleChatMessage, listGlobalChatMessages } from '@/lib/chat-server';
import { createServerSupabaseClient } from '@/lib/serverSupabase';

/** Global dashboard AI assistant chat. */
export async function GET() {
  try {
    const supabase = await createServerSupabaseClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();

    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const messages = await listGlobalChatMessages(supabase, user.id);
    return NextResponse.json({ success: true, messages });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Failed to load chat' },
      { status: 500 },
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const supabase = await createServerSupabaseClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();

    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const body = await request.json();
    const { message } = body;

    if (!message || typeof message !== 'string') {
      return NextResponse.json({ error: 'No message provided' }, { status: 400 });
    }

    const { userMessage, assistantMessage } = await handleChatMessage(
      supabase,
      user.id,
      message,
    );

    return NextResponse.json({
      success: true,
      messages: [userMessage, assistantMessage],
      message: assistantMessage,
    });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Chat request failed' },
      { status: 500 },
    );
  }
}
