/** Maps to the live `timeline_tasks` Supabase table. */
export interface TimelineTask {
  id: string;
  application_id: string;
  completed: boolean;
  created_at: string;
  due_date: string | null;
}

/** Payload for creating a timeline task row. */
export interface TimelineTaskInsert {
  application_id: string;
  completed?: boolean;
  due_date?: string | null;
  created_at?: string;
}

/** Payload for updating timeline task completion or due date. */
export type TimelineTaskUpdate = Partial<
  Pick<TimelineTask, 'completed' | 'due_date'>
>;

/** Lightweight shape used in analysis results and dashboard widgets. */
export interface TimelineEventSummary {
  date: string;
  event: string;
}
