import { Component, OnInit, OnDestroy } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { JobPollingService } from './job-polling.service';

/**
 * Example: GenerationComponent
 * Shows how to use the JobPollingService to monitor a generation job
 */

@Component({
  selector: 'app-generation',
  template: `
    <div class="generation-container">
      <!-- Status Display -->
      <div *ngIf="(jobPolling.jobStatus$ | async) as job">
        <h2>{{ job.status === 'completed' ? '✅ Complete!' : job.status === 'failed' ? '❌ Failed' : '⏳ Generating...' }}</h2>
        
        <!-- Progress Bar -->
        <div class="progress-bar">
          <div class="progress-fill" [style.width.%]="job.progress"></div>
        </div>
        <p class="progress-text">{{ job.progress }}% - Stage: {{ job.current_stage }}</p>

        <!-- Error Message -->
        <div *ngIf="job.status === 'failed'" class="error-message">
          {{ job.error || 'Generation failed' }}
        </div>

        <!-- Success Message -->
        <div *ngIf="job.status === 'completed'" class="success-message">
          Project generated successfully! ID: {{ job.result_data?.project_id }}
        </div>
      </div>

      <!-- Loading State -->
      <div *ngIf="!(jobPolling.jobStatus$ | async) && (jobPolling.isPolling$ | async)">
        <p>Initializing...</p>
      </div>

      <!-- Error Alert -->
      <div *ngIf="(jobPolling.pollingError$ | async) as error" class="error-alert">
        ⚠️ {{ error }}
      </div>
    </div>
  `,
  styles: [`
    .generation-container {
      padding: 20px;
      max-width: 500px;
    }

    .progress-bar {
      height: 24px;
      background: #e0e0e0;
      border-radius: 4px;
      overflow: hidden;
      margin: 20px 0;
    }

    .progress-fill {
      height: 100%;
      background: linear-gradient(90deg, #4caf50, #45a049);
      transition: width 0.3s ease;
    }

    .progress-text {
      text-align: center;
      font-size: 14px;
      color: #666;
    }

    .success-message {
      padding: 12px;
      background: #c8e6c9;
      color: #2e7d32;
      border-radius: 4px;
      margin-top: 12px;
    }

    .error-message {
      padding: 12px;
      background: #ffcdd2;
      color: #c62828;
      border-radius: 4px;
      margin-top: 12px;
    }

    .error-alert {
      padding: 12px;
      background: #fff3e0;
      color: #e65100;
      border-left: 4px solid #ff9800;
      margin-top: 12px;
    }
  `]
})
export class GenerationComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();
  private apiBaseUrl = 'http://localhost:8000/api/v1';

  constructor(
    public jobPolling: JobPollingService,
    private http: HttpClient
  ) {}

  ngOnInit(): void {
    // Example: Submit a generation request
    this.submitGenerationRequest();
  }

  /**
   * Submit a generation request and start polling
   */
  private submitGenerationRequest(): void {
    const payload = {
      project_name: 'hotel-management-system',
      prompt: 'Create a full-stack Hotel Management System...',
      backend: 'springboot',
      frontend: 'angular',
      features: ['authentication', 'booking', 'admin-dashboard'],
      mode_preference: 'generate'
    };

    this.http.post<any>(`${this.apiBaseUrl}/generate`, payload)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response) => {
          console.log('Job created:', response.job_id);
          // Start polling for this job
          this.jobPolling.startPolling(response.job_id);
        },
        error: (error) => {
          console.error('Failed to submit generation:', error);
          this.jobPolling.pollingError$.next(error?.error?.detail || 'Failed to submit');
        }
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    this.jobPolling.stopPolling();
  }
}
