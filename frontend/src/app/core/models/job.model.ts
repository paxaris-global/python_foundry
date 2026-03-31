export enum JobStatus {
  Pending = 'pending',
  Running = 'running',
  Completed = 'completed',
  Failed = 'failed',
}

export interface Job {
  id: string;
  status: JobStatus;
  progress: number;
  current_stage: string;
  error: string | null;
  trace_id: string | null;
  cache_hit: boolean;
  project_id: string | null;
  stage_timings: Record<string, number>;
  result_data: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}
