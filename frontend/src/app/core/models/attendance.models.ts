export interface AttendanceDay {
  id: string;
  user_id: string;
  work_date: string;
  check_in_at: string;
  check_out_at: string | null;
}

export interface TeamAttendanceRow {
  user_id: string;
  full_name: string;
  employee_code: string | null;
  work_date: string;
  check_in_at: string | null;
  check_out_at: string | null;
}
