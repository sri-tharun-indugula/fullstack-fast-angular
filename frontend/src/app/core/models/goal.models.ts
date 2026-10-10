export type GoalStatus = 'not_started' | 'in_progress' | 'completed' | 'cancelled';

export interface PerformanceGoal {
  id: string;
  assignee_user_id: string;
  assignee_name: string;
  created_by_user_id: string | null;
  title: string;
  description: string;
  due_date: string | null;
  status: GoalStatus;
  progress_percent: number;
  manager_note: string | null;
  created_at: string;
  updated_at: string;
}

export interface GoalCreate {
  assignee_user_id: string;
  title: string;
  description: string;
  due_date?: string | null;
}

export interface GoalEmployeeUpdate {
  status?: GoalStatus;
  progress_percent?: number;
}

export interface GoalManagerUpdate {
  status?: GoalStatus;
  progress_percent?: number;
  manager_note?: string | null;
}
