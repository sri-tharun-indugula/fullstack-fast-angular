export type DocumentScope = 'company' | 'employee';

export interface HrDocument {
  id: string;
  scope: DocumentScope;
  owner_user_id: string | null;
  owner_name: string | null;
  uploaded_by_user_id: string;
  uploaded_by_name: string;
  title: string;
  description: string | null;
  original_filename: string;
  content_type: string;
  size_bytes: number;
  created_at: string;
}
