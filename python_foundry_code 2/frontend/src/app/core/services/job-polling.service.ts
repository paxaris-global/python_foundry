import { Injectable, inject } from '@angular/core';
import { Observable, timer } from 'rxjs';
import { switchMap, takeWhile, distinctUntilChanged } from 'rxjs/operators';
import { GenerationApiService } from './generation-api.service';
import { Job, JobStatus } from '@core/models';
import { environment } from '@env';

@Injectable({ providedIn: 'root' })
export class JobPollingService {
  private readonly api = inject(GenerationApiService);

  /**
   * Polls GET /jobs/{jobId} at fixed intervals until the job reaches
   * a terminal state (completed or failed). Each intermediate state
   * change is emitted so the UI can update progress in real time.
   */
  pollUntilDone(jobId: string): Observable<Job> {
    return timer(0, environment.pollingIntervalMs).pipe(
      switchMap(() => this.api.getJob(jobId)),
      distinctUntilChanged((prev, curr) => {
        try {
          return (
            prev.progress === curr.progress &&
            prev.status === curr.status &&
            prev.current_stage === curr.current_stage &&
            JSON.stringify(prev.stage_timings) === JSON.stringify(curr.stage_timings)
          );
        } catch (_e) {
          return prev.progress === curr.progress && prev.status === curr.status;
        }
      }),
      takeWhile(
        (job) =>
          job.status !== JobStatus.Completed && job.status !== JobStatus.Failed,
        true // include the terminal emission
      )
    );
  }
}
