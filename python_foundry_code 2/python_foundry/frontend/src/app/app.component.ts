import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet],
  template: `
    <header class="app-header">
      <div class="header-content">
        <h1 class="logo">⚡ AI CodeGen Platform</h1>
        <span class="tagline">Generate full-stack projects from natural language</span>
      </div>
    </header>
    <main class="app-main">
      <router-outlet />
    </main>
  `,
  styles: [`
    .app-header {
      background: var(--color-surface);
      border-bottom: 1px solid var(--color-border);
      padding: 16px 24px;
    }
    .header-content {
      max-width: 960px;
      margin: 0 auto;
      display: flex;
      align-items: baseline;
      gap: 16px;
      flex-wrap: wrap;
    }
    .logo {
      margin: 0;
      font-size: 1.4rem;
      font-weight: 700;
    }
    .tagline {
      color: var(--color-text-muted);
      font-size: 0.9rem;
    }
    .app-main {
      max-width: 960px;
      margin: 32px auto;
      padding: 0 24px;
    }
  `],
})
export class AppComponent {}
