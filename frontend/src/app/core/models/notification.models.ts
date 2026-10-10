export type NotificationKind =
  | 'leave_submitted'
  | 'leave_approved'
  | 'leave_rejected'
  | 'goal_assigned'
  | 'document_available';

export interface AppNotification {
  id: string;
  kind: NotificationKind;
  title: string;
  body: string;
  entity_type: string | null;
  entity_id: string | null;
  read_at: string | null;
  created_at: string;
}

export interface UnreadCount {
  count: number;
}
