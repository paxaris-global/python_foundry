import { Component, input, output } from '@angular/core';
import { KeyValuePipe } from '@angular/common';
import { Job } from '@core/models';
import { ProgressBarComponent } from '@shared/components/progress-bar/progress-bar.component';
import { StageLabelPipe } from '@shared/pipes/stage-label.pipe';

@Component({
  selector: 'app-job-progress',
  standalone: true,
  imports: [ProgressBarComponent, StageLabelPipe, KeyValuePipe],
  template: `
    <div class="card progress-card">
      <h2>Generating Project...</h2>

      @if (job(); as j) {
        <app-progress-bar [value]="j.progress" />

        <div class="meta">
          <div class="stage">
            <span class="label">Stage:</span>
            <span class="value">{{ j.current_stage | stageLabel }}</span>
          </div>
          <div class="status">
            <span class="label">Status:</span>
            <span class="value" [class]="j.status">{{ j.status }}</span>
          </div>
        </div>

        @if (objectKeys(j.stage_timings).length > 0) {
          <details class="timings">
            <summary>Stage Timings</summary>
            <ul>
              @for (entry of j.stage_timings | keyvalue; track entry.key) {
                <li>
                  <span class="timing-stage">{{ entry.key | stageLabel }}</span>
                  <span class="timing-value">{{ formatTiming(entry.value) }}</span>
                </li>
              }
            </ul>
          </details>
        }
      } @else {
        <p class="waiting">Waiting for job to start...</p>
      }

      <button class="secondary" (click)="cancelClicked.emit()">Cancel</button>
    </div>
  `,
  styles: [`
    .progress-card {
      display: flex;
      flex-direction: column;
      gap: 20px;
    }
    h2 { margin: 0; }
    .meta {
      display: flex;
      gap: 32px;
    }
    .label {
      color: var(--color-text-muted);
      font-size: 0.85rem;
      margin-right: 6px;
    }
    .value {
      font-weight: 600;
    }
    .pending  { color: var(--color-warning); }
    .running  { color: var(--color-primary); }
    .completed { color: var(--color-success); }
    .failed   { color: var(--color-error); }
    .timings {
      font-size: 0.9rem;
    }
    .timings summary {
      cursor: pointer;
      color: var(--color-text-muted);
    }
    .timings ul {
      list-style: none;
      padding: 0;
      margin: 8px 0 0;
    }
    .timings li {
      display: flex;
      justify-content: space-between;
      padding: 4px 0;
      border-bottom: 1px solid var(--color-surface-alt);
    }
    .timing-stage { color: var(--color-text); }
    .timing-value {
      color: var(--color-text-muted);
      font-variant-numeric: tabular-nums;
    }
    .waiting {
      color: var(--color-text-muted);
      font-style: italic;
    }
  `],
})
export class JobProgressComponent {
  job = input.required<Job | null>();
  cancelClicked = output();

  objectKeys = Object.keys;

  formatTiming(value: unknown): string {
    const num = Number(value);
    if (isNaN(num)) return String(value);
    return num < 1 ? `${(num * 1000).toFixed(0)}ms` : `${num.toFixed(1)}s`;
  }
}
