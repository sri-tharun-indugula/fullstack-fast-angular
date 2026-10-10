export type LeaveStatus = 'pending' | 'approved' | 'rejected' | 'cancelled';

export interface LeaveType {
  id: string;
  code: string;
  name: string;
  annual_quota: string;
  is_active: boolean;
}

export interface LeaveBalance {
  leave_type: LeaveType;
  year: number;
  entitled: string;
  used: string;
  pending: string;
  available: string;
}

export interface LeaveRequest {
  id: string;
  user_id: string;
  employee_name: string;
  leave_type: LeaveType;
  start_date: string;
  end_date: string;
  days: string;
  reason: string;
  status: LeaveStatus;
  reviewer_user_id: string | null;
  reviewed_at: string | null;
  reviewer_note: string | null;
  created_at: string;
}

export interface LeaveRequestCreate {
  leave_type_id: string;
  start_date: string;
  end_date: string;
  reason: string;
}
