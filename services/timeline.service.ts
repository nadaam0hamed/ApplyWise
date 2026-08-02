import { requireUserId } from '@/lib/auth-helpers';
import { TIMELINE_TASK_COLUMNS } from '@/lib/supabase-live-schema';
import { supabase } from '@/lib/supabase';
import type { TimelineTask, TimelineTaskInsert } from '@/types/timeline';

export const TimelineService = {
  async listByApplication(applicationId: string): Promise<TimelineTask[]> {
    const { data, error } = await supabase
      .from('timeline_tasks')
      .select(TIMELINE_TASK_COLUMNS)
      .eq('application_id', applicationId)
      .order('created_at', { ascending: true });

    if (error) throw new Error(error.message);
    return (data ?? []) as TimelineTask[];
  },

  async createDefaultsForApplication(
    applicationId: string,
    deadline: string | null,
  ): Promise<TimelineTask[]> {
    await requireUserId();

    if (!deadline) return [];

    const now = new Date().toISOString();
    const deadlineDate = new Date(deadline);

    const decisionDate = new Date(deadlineDate);
    decisionDate.setDate(decisionDate.getDate() + 21);

    const startDate = new Date(deadlineDate);
    startDate.setMonth(startDate.getMonth() + 2);

    const tasks: TimelineTaskInsert[] = [
      { application_id: applicationId, due_date: deadline, completed: false, created_at: now },
      {
        application_id: applicationId,
        due_date: decisionDate.toISOString().split('T')[0],
        completed: false,
        created_at: now,
      },
      {
        application_id: applicationId,
        due_date: startDate.toISOString().split('T')[0],
        completed: false,
        created_at: now,
      },
    ];

    const { data, error } = await supabase
      .from('timeline_tasks')
      .insert(tasks)
      .select(TIMELINE_TASK_COLUMNS);

    if (error) throw new Error(error.message);
    return (data ?? []) as TimelineTask[];
  },
};
