import type { SupabaseClient } from '@supabase/supabase-js';

import { RequirementCategory } from '@/constants/requirementCategories';
import {
  APPLICATION_COLUMNS,
  CHAT_HISTORY_COLUMNS,
  TIMELINE_TASK_COLUMNS,
} from '@/lib/supabase-live-schema';
import type { ApplicationContext } from '@/services/analysis.service';
import { generateChatResponse } from '@/services/analysis.service';
import type { ChatHistoryMessage, ChatResponseMessage } from '@/types/chat';

const WELCOME_MESSAGE =
  'Hello! I am your ApplyWise AI assistant. I can help you with your application process. Ask me anything about your documents, timeline, or recommendations.';

function toUiMessage(row: ChatHistoryMessage): ChatResponseMessage {
  return {
    id: row.id,
    type: row.role === 'user' ? 'user' : 'assistant',
    content: row.message,
    timestamp: row.created_at,
  };
}

async function getLatestApplicationId(
  supabase: SupabaseClient,
  userId: string,
): Promise<string | null> {
  const { data, error } = await supabase
    .from('applications')
    .select('id')
    .eq('user_id', userId)
    .order('created_at', { ascending: false })
    .limit(1)
    .maybeSingle();

  if (error) throw new Error(`Failed to fetch applications: ${error.message}`);
  return data?.id ?? null;
}

async function assertApplicationOwnership(
  supabase: SupabaseClient,
  applicationId: string,
  userId: string,
): Promise<void> {
  const { data, error } = await supabase
    .from('applications')
    .select('id')
    .eq('id', applicationId)
    .eq('user_id', userId)
    .maybeSingle();

  if (error) throw new Error(`Failed to verify application ownership: ${error.message}`);
  if (!data) throw new Error('Application not found or you do not have access to it');
}

async function getApplicationContextForServer(
  supabase: SupabaseClient,
  applicationId: string,
  userId: string,
): Promise<ApplicationContext | null> {
  const { data: application, error: appError } = await supabase
    .from('applications')
    .select('id,user_id,title,readiness_score')
    .eq('id', applicationId)
    .eq('user_id', userId)
    .maybeSingle();

  if (appError) throw new Error(`Failed to fetch application: ${appError.message}`);
  if (!application) return null;

  const [documentsResult, requirementsResult, timelineResult, analysisResult] = await Promise.all([
    supabase
      .from('documents')
      .select('file_name,document_type')
      .eq('application_id', applicationId)
      .order('uploaded_at', { ascending: false }),
    supabase
      .from('requirements')
      .select('id,category')
      .eq('application_id', applicationId),
    supabase
      .from('timeline_tasks')
      .select(TIMELINE_TASK_COLUMNS)
      .eq('application_id', applicationId)
      .order('created_at', { ascending: true }),
    supabase
      .from('ai_analysis')
      .select('readiness_score,recommendations')
      .eq('application_id', applicationId)
      .order('created_at', { ascending: false })
      .limit(1)
      .maybeSingle(),
  ]);

  if (documentsResult.error) throw new Error(`Failed to fetch documents: ${documentsResult.error.message}`);
  if (requirementsResult.error) throw new Error(`Failed to fetch requirements: ${requirementsResult.error.message}`);
  if (timelineResult.error) {
    if (timelineResult.error.message.includes('row-level security policy')) {
      console.error('RLS policy blocking timeline access');
      // Continue with the data we have
    } else {
      throw new Error(`Failed to fetch timeline: ${timelineResult.error.message}`);
    }
  }

  const requirementIds = (requirementsResult.data ?? []).map((row) => row.id);
  let statusMap = new Map<string, string>();

  if (requirementIds.length > 0) {
    const { data: statuses, error: statusError } = await supabase
      .from('requirement_status')
      .select('requirement_id,status')
      .in('requirement_id', requirementIds);

    if (statusError) throw new Error(`Failed to fetch requirement statuses: ${statusError.message}`);
    statusMap = new Map(
      (statuses ?? []).map((row) => [row.requirement_id, row.status as string]),
    );
  }

  const docReqs = (requirementsResult.data ?? []).filter(
    (row) => row.category === RequirementCategory.Documents,
  );
  const uploadedDocuments = (documentsResult.data ?? []).map((doc) => doc.file_name);
  const missingDocuments = docReqs
    .filter((req) => statusMap.get(req.id) !== 'fulfilled')
    .map((req) => req.category);

  const timelineTasks = timelineResult.data ?? [];
  const nextDeadline =
    timelineTasks.find((task) => task.due_date && !task.completed)?.due_date ?? null;
  const daysUntilDeadline = nextDeadline
    ? Math.ceil((new Date(nextDeadline).getTime() - Date.now()) / (1000 * 60 * 60 * 24))
    : null;

  // Extract actual data from analysis/report if available
  let actualGPA: string | null = null;
  let actualIELTS: string | null = null;
  let actualReadinessScore: number | null = null;
  let actualStrengths: string[] = [];
  let actualWeaknesses: string[] = [];
  let applicantProfile: any = null;

  if (analysisResult.data) {
    try {
      const analysis = analysisResult.data;
      if (analysis.recommendations) {
        const recs = typeof analysis.recommendations === 'string' 
          ? JSON.parse(analysis.recommendations) 
          : analysis.recommendations;
        
        if (recs && typeof recs === 'object') {
          actualReadinessScore = recs.eligibility_score ?? recs.readiness_score ?? null;
          actualStrengths = Array.isArray(recs.strengths) ? recs.strengths : [];
          actualWeaknesses = Array.isArray(recs.weaknesses) ? recs.weaknesses : [];
          
          // Try to extract GPA from document evaluations
          if (recs.document_evaluations && Array.isArray(recs.document_evaluations)) {
            const transcript = recs.document_evaluations.find((doc: any) => 
              doc.name?.toLowerCase().includes('transcript') || 
              doc.name?.toLowerCase().includes('marksheet')
            );
            if (transcript?.extracted_information) {
              actualGPA = transcript.extracted_information.gpa || transcript.extracted_information.GPA || null;
            }
            
            const ielts = recs.document_evaluations.find((doc: any) => 
              doc.name?.toLowerCase().includes('ielts') || 
              doc.name?.toLowerCase().includes('english')
            );
            if (ielts?.extracted_information) {
              actualIELTS = ielts.extracted_information.score || ielts.extracted_information.overall_score || null;
            }
          }
          
          // Try to get applicant profile summary
          if (recs.readiness_report) {
            const report = typeof recs.readiness_report === 'string' 
              ? JSON.parse(recs.readiness_report) 
              : recs.readiness_report;
            if (report?.applicant_profile_summary) {
              applicantProfile = report.applicant_profile_summary;
            }
          }
        }
      }
    } catch (e) {
      console.error('Failed to parse analysis recommendations:', e);
    }
  }

  return {
    readinessScore: actualReadinessScore ?? application.readiness_score,
    programName: application.title,
    deadline: nextDeadline,
    missingDocuments,
    uploadedDocuments,
    daysUntilDeadline,
    // Add actual data
    actualGPA,
    actualIELTS,
    actualStrengths,
    actualWeaknesses,
    applicantProfile,
  };
}

async function insertMessage(
  supabase: SupabaseClient,
  applicationId: string,
  role: 'user' | 'assistant',
  message: string,
): Promise<ChatHistoryMessage> {
  const { data, error } = await supabase
    .from('chat_history')
    .insert({
      application_id: applicationId,
      role,
      message,
      created_at: new Date().toISOString(),
    })
    .select(CHAT_HISTORY_COLUMNS)
    .single();

  if (error) {
    console.error('Chat insert error:', error);
    // Return a fallback local message if insert fails
    return {
      id: `local-${role}-${Date.now()}`,
      application_id: applicationId,
      role,
      message,
      created_at: new Date().toISOString(),
    } as ChatHistoryMessage;
  }
  return data as ChatHistoryMessage;
}

export async function handleChatMessage(
  supabase: SupabaseClient,
  userId: string,
  message: string,
  applicationId?: string | null,
): Promise<{
  userMessage: ChatResponseMessage;
  assistantMessage: ChatResponseMessage;
}> {
  const trimmed = message.trim();
  if (!trimmed) {
    throw new Error('Message cannot be empty');
  }

  let resolvedApplicationId = applicationId ?? null;

  if (resolvedApplicationId) {
    await assertApplicationOwnership(supabase, resolvedApplicationId, userId);
  } else {
    resolvedApplicationId = await getLatestApplicationId(supabase, userId);
  }

  if (!resolvedApplicationId) {
    const assistantContent =
      'I do not have an active application yet. Start a new application from the dashboard to get personalized guidance.';
    return {
      userMessage: {
        id: `local-user-${Date.now()}`,
        type: 'user',
        content: trimmed,
        timestamp: new Date().toISOString(),
      },
      assistantMessage: {
        id: `local-assistant-${Date.now()}`,
        type: 'assistant',
        content: assistantContent,
        timestamp: new Date().toISOString(),
      },
    };
  }

  const userRow = await insertMessage(supabase, resolvedApplicationId, 'user', trimmed);
  const context = await getApplicationContextForServer(
    supabase,
    resolvedApplicationId,
    userId,
  );
  const assistantContent = generateChatResponse(trimmed, context);
  const assistantRow = await insertMessage(
    supabase,
    resolvedApplicationId,
    'assistant',
    assistantContent,
  );

  return {
    userMessage: toUiMessage(userRow),
    assistantMessage: toUiMessage(assistantRow),
  };
}

export async function listChatMessages(
  supabase: SupabaseClient,
  userId: string,
  applicationId: string,
): Promise<ChatResponseMessage[]> {
  await assertApplicationOwnership(supabase, applicationId, userId);

  const { data, error } = await supabase
    .from('chat_history')
    .select(CHAT_HISTORY_COLUMNS)
    .eq('application_id', applicationId)
    .order('created_at', { ascending: true });

  if (error) throw new Error(`Failed to load chat messages: ${error.message}`);

  const rows = (data ?? []) as ChatHistoryMessage[];
  if (rows.length === 0) {
    const welcome = await insertMessage(
      supabase,
      applicationId,
      'assistant',
      WELCOME_MESSAGE,
    );
    return [toUiMessage(welcome)];
  }

  return rows.map(toUiMessage);
}

export async function listGlobalChatMessages(
  supabase: SupabaseClient,
  userId: string,
): Promise<ChatResponseMessage[]> {
  const applicationId = await getLatestApplicationId(supabase, userId);

  if (!applicationId) {
    return [
      {
        id: 'welcome',
        type: 'assistant',
        content: WELCOME_MESSAGE,
        timestamp: new Date().toISOString(),
      },
    ];
  }

  return listChatMessages(supabase, userId, applicationId);
}

export { WELCOME_MESSAGE };
