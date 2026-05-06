import { Component, input } from '@angular/core';

@Component({
  selector: 'app-progress-bar',
  standalone: true,
  template: `
    <div class="track">
      <div
        class="fill"
        [style.width.%]="value()"
        [class.complete]="value() >= 100"
      ></div>
    </div>
    <span class="label">{{ value() }}%</span>
  `,
  styles: [`
    :host {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .track {
      flex: 1;
      height: 10px;
      background: var(--color-surface-alt);
      border-radius: 5px;
      overflow: hidden;
    }
    .fill {
      height: 100%;
      background: var(--color-primary);
      border-radius: 5px;
      transition: width 0.4s ease;
    }
    .fill.complete {
      background: var(--color-success);
    }
    .label {
      font-size: 0.85rem;
      color: var(--color-text-muted);
      min-width: 40px;
      text-align: right;
    }
  `],
})
export class ProgressBarComponent {
  value = input.required<number>();
}
