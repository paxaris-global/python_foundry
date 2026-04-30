import { Injectable, OnDestroy } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Subject, timer } from 'rxjs';
import { switchMap, takeUntil, takeWhile, tap, catchError } from 'rxjs/operators';
import { of } from 'rxjs';

/**
 * JobPollingService - Safely polls generation job status without blocking the UI thread
 * 
 * Features:
 * - RxJS-based polling (every 2.5 seconds, not 100ms)
 * - switchMap prevents overlapping requests
 * - Proper cleanup on component destroy
 * - Observable pattern, no setInterval
 */

export interface JobStatus {
  id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  current_stage: string;
  result_data?: any;
  error?: string;
}

@Injectable({
  providedIn: 'root'
})
export class JobPollingService implements OnDestroy {
  private apiBaseUrl = 'http://localhost:8000/api/v1';
  private destroy$ = new Subject<void>();

  // Observable streams
  public jobStatus$ = new BehaviorSubject<JobStatus | null>(null);
  public isPolling$ = new BehaviorSubject<boolean>(false);
  public pollingError$ = new BehaviorSubject<string | null>(null);

  constructor(private http: HttpClient) {}

  /**
   * Start polling a job until it completes or fails
   * @param jobId - UUID of the generation job
   */
  startPolling(jobId: string): void {
    if (!jobId) {
      this.pollingError$.next('Invalid job ID');
      return;
    }

    this.isPolling$.next(true);
    this.pollingError$.next(null);

    // Poll every 2.5 seconds (instead of 100ms)
    timer(0, 2500)
      .pipe(
        // Make HTTP request
        switchMap(() =>
          this.http.get<JobStatus>(`${this.apiBaseUrl}/jobs/${jobId}`).pipe(
            catchError(error => {
              console.error('Poll error:', error);
              this.pollingError$.next(error?.error?.detail || 'Failed to fetch job status');
              return of(null);
            })
          )
        ),
        // Filter out null responses from errors
        takeWhile(job => job !== null && (job.status === 'pending' || job.status === 'running'), true),
        // Stop polling when destroy signal is sent
        takeUntil(this.destroy$),
        // Update the status stream
        tap(job => {
          if (job) {
            this.jobStatus$.next(job);

            // Automatically stop polling when job completes
            if (job.status === 'completed' || job.status === 'failed') {
              this.stopPolling();
            }
          }
        })
      )
      .subscribe({
        next: () => {
          // Silent success - status is updated in tap()
        },
        error: (err) => {
          console.error('Polling subscription error:', err);
          this.pollingError$.next('Polling error: ' + (err?.message || 'Unknown error'));
          this.isPolling$.next(false);
        },
        complete: () => {
          this.isPolling$.next(false);
        }
      });
  }

  /**
   * Stop polling immediately
   */
  stopPolling(): void {
    this.isPolling$.next(false);
    this.destroy$.next();
  }

  /**
   * Get current job status
   */
  getCurrentStatus(): JobStatus | null {
    return this.jobStatus$.value;
  }

  /**
   * Reset the service state
   */
  reset(): void {
    this.jobStatus$.next(null);
    this.pollingError$.next(null);
    this.isPolling$.next(false);
    this.destroy$.next();
  }

  /**
   * Cleanup on service destroy
   */
  ngOnDestroy(): void {
    this.stopPolling();
  }
}
