export interface DepartmentHeadcount {
  department_id: string | null;
  department_name: string;
  employee_count: number;
}

export interface ReportsOverview {
  total_employees: number;
  headcount_by_department: DepartmentHeadcount[];
  pending_leave_requests: number;
  checked_in_today: number;
}

export interface TeamReportsOverview {
  direct_reports: number;
  pending_leave_requests: number;
  checked_in_today: number;
}
