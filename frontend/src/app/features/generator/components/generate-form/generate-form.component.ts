import { Component, output } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { GenerateRequest, ModePreference } from '@core/models';

@Component({
  selector: 'app-generate-form',
  standalone: true,
  imports: [FormsModule],
  template: `
    <form (ngSubmit)="onSubmit()" class="card form-grid">
      <h2 class="form-title">Generate a New Project</h2>

      <div class="field">
        <label for="projectName">Project Name *</label>
        <input
          id="projectName"
          [(ngModel)]="projectName"
          name="projectName"
          placeholder="e.g. hotel-management-system"
          required
          minlength="2"
          maxlength="120"
        />
      </div>

      <div class="field">
        <label for="prompt">Prompt</label>
        <textarea
          id="prompt"
          [(ngModel)]="prompt"
          name="prompt"
          rows="4"
          placeholder="Describe your project... e.g. Build a CRM with auth, dashboard, customer CRUD and reports"
        ></textarea>
      </div>

      <div class="row">
        <div class="field">
          <label for="backend">Backend</label>
          <select id="backend" [(ngModel)]="backend" name="backend">
            <option value="springboot">Spring Boot</option>
          </select>
        </div>
        <div class="field">
          <label for="frontend">Frontend</label>
          <select id="frontend" [(ngModel)]="frontend" name="frontend">
            <option value="angular">Angular</option>
          </select>
        </div>
      </div>

      <div class="field">
        <label for="features">Features (comma separated)</label>
        <input
          id="features"
          [(ngModel)]="featuresRaw"
          name="features"
          placeholder="auth, dashboard, crud, reports"
        />
      </div>

      <div class="row">
        <div class="field">
          <label for="websiteLike">Website Like (optional URL)</label>
          <input
            id="websiteLike"
            [(ngModel)]="websiteLike"
            name="websiteLike"
            placeholder="https://example.com"
          />
        </div>
        <div class="field">
          <label for="mode">Mode Preference</label>
          <select id="mode" [(ngModel)]="modePreference" name="mode">
            <option value="auto">Auto</option>
            <option value="reuse">Reuse</option>
            <option value="adapt">Adapt</option>
            <option value="generate">Generate</option>
            <option value="hybrid_scaffold">Hybrid Scaffold</option>
          </select>
        </div>
      </div>

      <button type="submit" class="primary submit-btn" [disabled]="!projectName.trim()">
        Generate Project
      </button>
    </form>
  `,
  styles: [`
    .form-grid {
      display: flex;
      flex-direction: column;
      gap: 20px;
    }
    .form-title {
      margin: 0 0 4px;
      font-size: 1.3rem;
    }
    .field {
      display: flex;
      flex-direction: column;
      gap: 6px;
      flex: 1;
    }
    .field label {
      font-size: 0.85rem;
      color: var(--color-text-muted);
      font-weight: 600;
    }
    .row {
      display: flex;
      gap: 16px;
    }
    .submit-btn {
      align-self: flex-start;
      padding: 12px 32px;
      font-size: 1rem;
    }
  `],
})
export class GenerateFormComponent {
  submitReq = output<GenerateRequest>();

  projectName = '';
  prompt = '';
  backend: 'springboot' = 'springboot';
  frontend: 'angular' = 'angular';
  featuresRaw = '';
  websiteLike = '';
  modePreference: ModePreference = 'auto';

  onSubmit(): void {
    const features = this.featuresRaw
      .split(',')
      .map((f) => f.trim())
      .filter(Boolean);

    const req: GenerateRequest = {
      project_name: this.projectName.trim(),
      backend: this.backend,
      frontend: this.frontend,
      features,
      mode_preference: this.modePreference,
    };

    if (this.prompt.trim()) {
      req.prompt = this.prompt.trim();
    }
    if (this.websiteLike.trim()) {
      req.website_like = this.websiteLike.trim();
    }

    this.submitReq.emit(req);
  }
}
