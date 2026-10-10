export interface Department {
  id: string;
  name: string;
  code: string;
  parent_id: string | null;
}

export interface EmployeeProfile {
  id: string;
  user_id: string;
  email: string;
  full_name: string;
  role: string;
  employee_code: string;
  job_title: string;
  phone: string | null;
  work_location: string | null;
  joined_on: string | null;
  department: Department | null;
  manager_user_id: string | null;
  manager_full_name: string | null;
}

export interface DepartmentCreate {
  name: string;
  code: string;
  parent_id?: string | null;
}

export interface EmployeeSelfUpdate {
  phone?: string | null;
  work_location?: string | null;
}
