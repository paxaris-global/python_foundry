import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '@env';
import { GenerateRequest, GenerateResponse, Job, Project } from '@core/models';

@Injectable({ providedIn: 'root' })
export class GenerationApiService {
  private readonly http = inject(HttpClient);
  private readonly base = environment.apiBaseUrl;

  generate(req: GenerateRequest): Observable<GenerateResponse> {
    return this.http.post<GenerateResponse>(`${this.base}/generate`, req);
  }

  getJob(jobId: string): Observable<Job> {
    return this.http.get<Job>(`${this.base}/jobs/${jobId}`);
  }

  getProject(projectId: string): Observable<Project> {
    return this.http.get<Project>(`${this.base}/projects/${projectId}`);
  }

  downloadProject(projectId: string): Observable<Blob> {
    return this.http.get(`${this.base}/projects/${projectId}/download`, {
      responseType: 'blob',
    });
  }

  getHealth(): Observable<Record<string, unknown>> {
    return this.http.get<Record<string, unknown>>(`${this.base}/health`);
  }
}
