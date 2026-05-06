import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { GeneratorStore } from '../../state/generator.store';
import { GenerateFormComponent } from '../../components/generate-form/generate-form.component';
import { JobProgressComponent } from '../../components/job-progress/job-progress.component';
import { ProjectResultComponent } from '../../components/project-result/project-result.component';

@Component({
  selector: 'app-generator-page',
  standalone: true,
  providers: [GeneratorStore],
  imports: [CommonModule, GenerateFormComponent, JobProgressComponent, ProjectResultComponent],
  template: `
    <!-- Only show progress bar and job progress after generation starts -->
    <app-job-progress
      *ngIf="store.phase() === 'submitting' || store.phase() === 'polling' || store.job()"
      [job]="store.job()"
      (cancelClicked)="store.cancel()"
    />

    @switch (store.phase()) {
      @case ('idle') {
        <app-generate-form (submitReq)="store.generate($event)" />
      }
      @case ('error') {
        <div class="card error-card">
          <h2>Generation Failed</h2>
          <p class="error-msg">{{ store.error() }}</p>
          <button class="primary" (click)="store.newGeneration()">Try Again</button>
        </div>
      }
    }

    <!-- Show project result card below progress bar when done -->
    <app-project-result
      *ngIf="store.phase() === 'done' && store.project()"
      [project]="store.project()"
      [isDownloading]="store.downloading()"
      (downloadClicked)="store.downloadZip()"
      (newGenerationClicked)="store.newGeneration()"
    />
  `,
  styles: [`
    .status-card {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 16px;
      text-align: center;
    }
    .status-card p {
      color: var(--color-text-muted);
      margin: 0;
    }
    .spinner {
      width: 40px;
      height: 40px;
      border: 3px solid var(--color-surface-alt);
      border-top-color: var(--color-primary);
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
    }
    @keyframes spin {
      to { transform: rotate(360deg); }
    }
    .error-card {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    .error-card h2 {
      margin: 0;
      color: var(--color-error);
    }
    .error-msg {
      color: var(--color-text-muted);
      margin: 0;
      padding: 12px;
      background: rgba(239, 68, 68, 0.1);
      border-radius: var(--radius);
      font-family: monospace;
      font-size: 0.9rem;
      white-space: pre-wrap;
      word-break: break-word;
    }
  `],
})
export class GeneratorPageComponent {
  protected readonly store = inject(GeneratorStore);
}
