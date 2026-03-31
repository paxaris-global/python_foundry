export type ModePreference = 'auto' | 'reuse' | 'adapt' | 'generate' | 'hybrid_scaffold';

export interface GenerateRequest {
  project_name: string;
  prompt?: string;
  backend: 'springboot';
  frontend: 'angular';
  features: string[];
  website_like?: string;
  mode_preference: ModePreference;
}

export interface GenerateResponse {
  job_id: string;
  status: string;
  fingerprint: string;
  cache_hit: boolean;
  cached_project_id: string | null;
  mode_selected: string | null;
}
