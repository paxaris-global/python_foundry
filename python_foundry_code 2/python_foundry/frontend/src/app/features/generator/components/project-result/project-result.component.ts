import { Component, input, output } from '@angular/core';
import { Project } from '@core/models';

@Component({
  selector: 'app-project-result',
  standalone: true,
  template: `
    @if (project(); as p) {
      <div class="card result-card">
        <div class="header">
          <h2>{{ p.name }}</h2>
          <span class="badge">{{ p.domain }}</span>
        </div>

        <p class="description">{{ p.description }}</p>

        <div class="info-grid">
          <div class="info-item">
            <span class="label">Backend</span>
            <span class="value">{{ p.backend_stack }}</span>
          </div>
          <div class="info-item">
            <span class="label">Frontend</span>
            <span class="value">{{ p.frontend_stack }}</span>
          </div>
          <div class="info-item">
            <span class="label">Files Generated</span>
            <span class="value">{{ p.generated_files.length }}</span>
          </div>
          @if (p.blueprint_used) {
            <div class="info-item">
              <span class="label">Blueprint</span>
              <span class="value">{{ p.blueprint_used }}</span>
            </div>
          }
        </div>

        @if (validationStatus(p); as vs) {
          <div class="validation" [class]="vs.cls">
            {{ vs.text }}
          </div>
        }

        @if (p.generated_files.length > 0) {
          <details class="files-list">
            <summary>Generated Files ({{ p.generated_files.length }})</summary>
            <ul>
              @for (file of p.generated_files; track file) {
                <li>{{ file }}</li>
              }
            </ul>
          </details>
        }

        <div class="actions">
          <button class="primary" (click)="downloadClicked.emit()" [disabled]="isDownloading()">
            {{ isDownloading() ? 'Downloading...' : 'Download ZIP' }}
          </button>
          <button class="secondary" (click)="newGenerationClicked.emit()">
            New Generation
          </button>
        </div>
      </div>
    }
  `,
  styles: [`
    .result-card {
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    .header {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .header h2 {
      margin: 0;
    }
    .badge {
      background: var(--color-surface-alt);
      padding: 2px 10px;
      border-radius: 12px;
      font-size: 0.8rem;
      color: var(--color-text-muted);
    }
    .description {
      color: var(--color-text-muted);
      margin: 0;
    }
    .info-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
      gap: 12px;
    }
    .info-item {
      background: var(--color-surface-alt);
      padding: 10px 14px;
      border-radius: var(--radius);
    }
    .info-item .label {
      display: block;
      font-size: 0.75rem;
      color: var(--color-text-muted);
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 2px;
    }
    .info-item .value {
      font-weight: 600;
    }
    .validation {
      padding: 10px 14px;
      border-radius: var(--radius);
      font-size: 0.9rem;
      font-weight: 600;
    }
    .validation.pass {
      background: rgba(34, 197, 94, 0.15);
      color: var(--color-success);
    }
    .validation.warn {
      background: rgba(245, 158, 11, 0.15);
      color: var(--color-warning);
    }
    .files-list summary {
      cursor: pointer;
      color: var(--color-text-muted);
      font-size: 0.9rem;
    }
    .files-list ul {
      max-height: 300px;
      overflow-y: auto;
      list-style: none;
      padding: 0;
      margin: 8px 0 0;
      font-size: 0.85rem;
      font-family: 'SF Mono', 'Fira Code', monospace;
    }
    .files-list li {
      padding: 3px 0;
      border-bottom: 1px solid var(--color-surface-alt);
    }
    .actions {
      display: flex;
      gap: 12px;
      padding-top: 8px;
    }
  `],
})
export class ProjectResultComponent {
  project = input.required<Project | null>();
  isDownloading = input(false);
  downloadClicked = output();
  newGenerationClicked = output();

  validationStatus(p: Project): { cls: string; text: string } | null {
    const report = p.validation_report;
    if (!report || Object.keys(report).length === 0) return null;

    const errors = (report['errors'] as string[] | undefined) ?? [];
    const warnings = (report['warnings'] as string[] | undefined) ?? [];

    if (errors.length > 0) {
      return { cls: 'warn', text: `Validation: ${errors.length} error(s), ${warnings.length} warning(s)` };
    }
    return { cls: 'pass', text: 'Validation passed' };
  }
}
