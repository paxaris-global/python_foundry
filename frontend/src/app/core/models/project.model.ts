export interface Project {
  id: string;
  name: string;
  description: string;
  backend_stack: string;
  frontend_stack: string;
  domain: string;
  blueprint_used: string | null;
  project_path: string;
  zip_path: string;
  manifest: Record<string, unknown>;
  rag_summary: Record<string, unknown>;
  cache_info: Record<string, unknown>;
  generated_files: string[];
  validation_report: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}
