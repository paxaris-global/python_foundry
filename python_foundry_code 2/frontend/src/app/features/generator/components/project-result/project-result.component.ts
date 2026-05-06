import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import type { Project } from '@core/models';

@Component({
  standalone: true,
  selector: 'app-project-result',
  templateUrl: './project-result.component.html',
  styleUrls: ['./project-result.component.scss'],
  imports: [CommonModule],
})
export class ProjectResultComponent {
  @Input() project: Project | null = null;
  @Input() isDownloading = false;
  @Output() downloadClicked = new EventEmitter<void>();
  @Output() newGenerationClicked = new EventEmitter<void>();

  get errors(): string[] {
    const report = this.project?.validation_report;
    const errs = report?.['errors'];
    return Array.isArray(errs) ? errs : [];
  }

  get warnings(): string[] {
    const report = this.project?.validation_report;
    const warns = report?.['warnings'];
    return Array.isArray(warns) ? warns : [];
  }

  validationStatus(p: Project | null): { cls: string; text: string } | null {
    if (!p) return null;
    const report = p.validation_report;
    if (!report || Object.keys(report).length === 0) return null;
    const errors = this.errors;
    const warnings = this.warnings;
    if (errors.length > 0) {
      return { cls: 'warn', text: `Validation: ${errors.length} error(s), ${warnings.length} warning(s)` };
    }
    return { cls: 'pass', text: 'Validation passed' };
  }

  hasWarningOrIncomplete(p: Project | null): boolean {
    if (!p) return false;
    // Accepts both orchestrator warning and validation_report['valid'] === false
    return (
      (p as any).warning ||
      (p.validation_report && p.validation_report['valid'] === false)
    );
  }
}
