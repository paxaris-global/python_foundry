import { Injectable, inject, signal, computed } from '@angular/core';
import { Subscription } from 'rxjs';
import { GenerationApiService } from '@core/services/generation-api.service';
import { JobPollingService } from '@core/services/job-polling.service';
import { DownloadService } from '@core/services/download.service';
import {
  GenerateRequest,
  GenerateResponse,
  Job,
  JobStatus,
  Project,
} from '@core/models';

export type Phase = 'idle' | 'submitting' | 'polling' | 'done' | 'error';

@Injectable()
export class GeneratorStore {
  private readonly api = inject(GenerationApiService);
  private readonly poller = inject(JobPollingService);
  private readonly dl = inject(DownloadService);
  private pollSub: Subscription | null = null;

  // --- state signals ---
  readonly phase = signal<Phase>('idle');
  readonly job = signal<Job | null>(null);
  readonly project = signal<Project | null>(null);
  readonly error = signal<string | null>(null);
  readonly downloading = signal(false);
  readonly generateResponse = signal<GenerateResponse | null>(null);

  readonly isTerminal = computed(
    () => this.phase() === 'done' || this.phase() === 'error'
  );

  // --- actions ---

  generate(req: GenerateRequest): void {
    this.reset();
    this.phase.set('submitting');

    this.api.generate(req).subscribe({
      next: (res) => {
        this.generateResponse.set(res);

        // Backend short-circuits on cache hit — skip polling
        if (res.cache_hit && res.cached_project_id) {
          this.loadProject(res.cached_project_id);
          return;
        }
        this.startPolling(res.job_id);
      },
      error: (err: Error) => this.fail(err.message),
    });
  }

  downloadZip(): void {
    const p = this.project();
    if (!p) return;

    this.downloading.set(true);
    this.dl.download(p.id, p.name).subscribe({
      next: () => this.downloading.set(false),
      error: (err: Error) => {
        this.downloading.set(false);
        console.error('Download failed:', err.message);
      },
    });
  }

  cancel(): void {
    this.pollSub?.unsubscribe();
    this.pollSub = null;
    this.phase.set('idle');
  }

  newGeneration(): void {
    this.reset();
  }

  // --- internals ---

  private startPolling(jobId: string): void {
    this.phase.set('polling');
    this.pollSub = this.poller.pollUntilDone(jobId).subscribe({
      next: (job) => {
        this.job.set(job);
        if (job.status === JobStatus.Completed && job.project_id) {
          this.loadProject(job.project_id);
        } else if (job.status === JobStatus.Failed) {
          this.fail(job.error ?? 'Generation failed');
        }
      },
      error: (err: Error) => this.fail(err.message),
    });
  }

  private loadProject(projectId: string): void {
    this.phase.set('polling'); // stay in polling while loading project metadata
    this.api.getProject(projectId).subscribe({
      next: (p) => {
        this.project.set(p);
        this.phase.set('done');
      },
      error: (err: Error) => this.fail(err.message),
    });
  }

  private fail(msg: string): void {
    this.error.set(msg);
    this.phase.set('error');
  }

  private reset(): void {
    this.pollSub?.unsubscribe();
    this.pollSub = null;
    this.phase.set('idle');
    this.job.set(null);
    this.project.set(null);
    this.error.set(null);
    this.generateResponse.set(null);
    this.downloading.set(false);
  }
}
