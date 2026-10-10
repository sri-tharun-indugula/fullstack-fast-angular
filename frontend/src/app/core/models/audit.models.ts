export type AuditAction =
  | 'auth.login_success'
  | 'auth.login_failed'
  | 'auth.logout'
  | 'leave.applied'
  | 'leave.approved'
  | 'leave.rejected'
  | 'goal.created'
  | 'document.uploaded'
  | 'document.deleted'
  | 'employee.created'
  | 'employee.updated';

export interface AuditLogEntry {
  id: string;
  actor_user_id: string | null;
  actor_email: string | null;
  action: AuditAction;
  entity_type: string | null;
  entity_id: string | null;
  summary: string;
  ip_address: string | null;
  metadata_json: Record<string, unknown> | null;
  created_at: string;
}

export interface AuditLogList {
  items: AuditLogEntry[];
  total: number;
  limit: number;
  offset: number;
}
