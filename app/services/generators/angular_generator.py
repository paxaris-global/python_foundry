from app.services.generators.base import BaseGenerator
from app.services.templates.jinja_renderer import JinjaRenderer
from app.services.templates.template_registry import TemplateRegistry


class AngularGenerator(BaseGenerator):
    def __init__(self) -> None:
        self.renderer = JinjaRenderer()

    def generate(self, project_spec: dict, api_contract: dict, rag_context: list[dict]) -> dict[str, str]:
        app_name = project_spec["project_name"]

        ctx = {
            "project_name": app_name,
            "api_base_url": "http://localhost:8080",
            "entity_name": "Customer",
        }

        files: dict[str, str] = {
            "frontend/package.json": self.renderer.render(TemplateRegistry.ANGULAR_PACKAGE_JSON.path, ctx),
            "frontend/angular.json": self.renderer.render(TemplateRegistry.ANGULAR_ANGULAR_JSON.path, ctx),
            "frontend/tsconfig.json": self._tsconfig_json(),
            "frontend/tsconfig.app.json": self._tsconfig_app_json(),
            "frontend/.gitignore": self._gitignore(),
            "frontend/src/main.ts": self._main_ts(),
            "frontend/src/index.html": self._index_html(app_name),
            "frontend/src/styles.css": self._styles_css(),
            "frontend/src/app/app.module.ts": self.renderer.render(TemplateRegistry.ANGULAR_APP_MODULE.path, ctx),
            "frontend/src/app/app-routing.module.ts": self.renderer.render(TemplateRegistry.ANGULAR_APP_ROUTING.path, ctx),
            "frontend/src/app/app.component.ts": self._app_component_ts(),
            "frontend/src/app/app.component.html": self._app_component_html(app_name),
            "frontend/src/app/app.component.css": self._app_component_css(),
            "frontend/src/app/core/services/api.service.ts": self.renderer.render(TemplateRegistry.ANGULAR_SERVICE.path, ctx),
            "frontend/src/app/features/customers/components/customer-list.component.ts": self.renderer.render(
                TemplateRegistry.ANGULAR_COMPONENT.path,
                ctx,
            ),
            "frontend/src/app/features/customers/components/customer-list.component.html": self.renderer.render(
              TemplateRegistry.ANGULAR_COMPONENT_HTML.path,
              ctx,
            ),
            "frontend/src/app/features/customers/components/customer-list.component.css": self._customer_component_css(),
            "frontend/src/app/features/customers/customers.module.ts": self._customers_module_ts(),
            "frontend/src/environments/environment.ts": self.renderer.render(
              TemplateRegistry.ANGULAR_ENVIRONMENT.path,
              {"production": False, "api_base_url": "http://localhost:8080/api/v1"},
            ),
            "frontend/src/environments/environment.prod.ts": self.renderer.render(
              TemplateRegistry.ANGULAR_ENVIRONMENT.path,
              {"production": True, "api_base_url": "/api"},
            ),
            "frontend/nginx.conf": self._nginx_conf(),
            "frontend/Dockerfile": self.renderer.render(TemplateRegistry.ANGULAR_DOCKERFILE.path, ctx),
            ".github/workflows/trigger.yml": self._trigger_workflow(),
        }
        return files

    @staticmethod
    def _tsconfig_json() -> str:
        return """{
  "compileOnSave": false,
  "compilerOptions": {
    "baseUrl": "./",
    "outDir": "./dist/out-tsc",
    "forceConsistentCasingInFileNames": true,
    "strict": true,
    "noImplicitOverride": true,
    "noPropertyAccessFromIndexSignature": false,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "sourceMap": true,
    "declaration": false,
    "experimentalDecorators": true,
    "moduleResolution": "bundler",
    "importHelpers": true,
    "target": "ES2022",
    "module": "ES2022",
    "useDefineForClassFields": false,
    "lib": ["ES2022", "dom"]
  },
  "angularCompilerOptions": {
    "enableI18nLegacyMessageIdFormat": false,
    "strictInjectionParameters": true,
    "strictInputAccessModifiers": true,
    "strictTemplates": true
  }
}
"""

    @staticmethod
    def _tsconfig_app_json() -> str:
        return """{
  "extends": "./tsconfig.json",
  "compilerOptions": {
    "outDir": "./out-tsc/app",
    "types": []
  },
  "files": ["src/main.ts"],
  "include": ["src/**/*.d.ts"]
}
"""

    @staticmethod
    def _gitignore() -> str:
        return """/node_modules
/dist
/.angular
/coverage
*.log
.DS_Store
Thumbs.db
"""

    @staticmethod
    def _trigger_workflow() -> str:
        return """name: Trigger Central CI/CD

on:
  push:
    branches:
      - main
      - master

jobs:
  trigger-central-workflow:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Central Workflow
        uses: peter-evans/repository-dispatch@v3
        with:
          token: ${{ secrets.GH_ACCESS_TOKEN }}
          repository: paxaris-global/paxo
          event-type: build-image
          client-payload: |
            {
              "repo": "${{ github.repository }}",
              "ref_name": "${{ github.ref_name }}",
              "ref": "${{ github.ref }}",
              "sha": "${{ github.sha }}"
            }
"""

    @staticmethod
    def _main_ts() -> str:
        return """import { platformBrowserDynamic } from '@angular/platform-browser-dynamic';
import { AppModule } from './app/app.module';

platformBrowserDynamic()
  .bootstrapModule(AppModule)
  .catch((err) => console.error(err));
"""

    @staticmethod
    def _index_html(app_name: str) -> str:
        return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <title>{app_name}</title>
  <base href=\"/\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
</head>
<body>
  <app-root></app-root>
</body>
</html>
"""

    @staticmethod
    def _styles_css() -> str:
        return """:root {
  --bg: #eaeded;
  --surface: #ffffff;
  --ink: #0f1111;
  --muted: #565959;
  --border: rgba(15, 17, 17, 0.12);

  /* Amazon/Flipkart-inspired accents (not identical) */
  --nav: #131921;
  --nav-2: #232f3e;
  --accent: #febd69;
  --accent-ink: #111111;
  --primary: #0a67ff;

  --radius: 14px;
}

html, body {
  margin: 0;
  font-family: Roboto, "Helvetica Neue", Arial, sans-serif;
  background: var(--bg);
  color: var(--ink);
}

* { box-sizing: border-box; }

/* App-wide helpers */
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 16px;
}
"""

    @staticmethod
    def _app_component_ts() -> str:
        return """import { Component } from '@angular/core';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  title = 'AI Generated App';
}
"""

    @staticmethod
    def _app_component_html(app_name: str) -> str:
        return f"""<div class="app-shell">
  <!-- Top navigation (storefront style) -->
  <header class="nav">
    <div class="nav-top">
      <div class="container nav-top-inner">
        <div class="brand" aria-label="{app_name} home">
          <span class="brand-mark">🛍️</span>
          <span class="brand-name">{app_name}</span>
        </div>

        <div class="nav-search" role="search">
          <mat-form-field appearance="outline" class="nav-search-field">
            <mat-label>Search</mat-label>
            <input matInput placeholder="Search items…" />
            <button mat-icon-button matSuffix type="button" aria-label="Search">
              <mat-icon>search</mat-icon>
            </button>
          </mat-form-field>
        </div>

        <div class="nav-actions">
          <button mat-button class="nav-action" type="button">
            <mat-icon>account_circle</mat-icon>
            <span class="nav-action-text">Account</span>
          </button>
          <button mat-button class="nav-action" type="button">
            <mat-icon>favorite_border</mat-icon>
            <span class="nav-action-text">Wishlist</span>
          </button>
          <button mat-flat-button class="nav-cart" type="button">
            <mat-icon>shopping_cart</mat-icon>
            <span class="nav-action-text">Cart</span>
          </button>
        </div>
      </div>
    </div>

    <div class="nav-bottom">
      <div class="container nav-bottom-inner">
        <button mat-button class="pill" type="button"><mat-icon>menu</mat-icon>All</button>
        <button mat-button class="pill" type="button">Deals</button>
        <button mat-button class="pill" type="button">Electronics</button>
        <button mat-button class="pill" type="button">Fashion</button>
        <button mat-button class="pill" type="button">Home</button>
        <span class="nav-spacer"></span>
        <span class="nav-note">Generated full-stack workspace</span>
      </div>
    </div>
  </header>

  <!-- Page content -->
  <main class="content">
    <div class="container">
      <router-outlet></router-outlet>
    </div>
  </main>
</div>
"""

    @staticmethod
    def _app_component_css() -> str:
        return """.app-shell { min-height: 100vh; }

.nav { position: sticky; top: 0; z-index: 1000; }

.nav-top { background: var(--nav); color: #fff; }
.nav-top-inner {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 10px 0;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 700;
  letter-spacing: 0.2px;
}
.brand-mark { font-size: 20px; }
.brand-name { white-space: nowrap; }

.nav-search { flex: 1; min-width: 200px; }
.nav-search-field { width: 100%; }
.nav-search-field ::ng-deep .mdc-notched-outline__leading,
.nav-search-field ::ng-deep .mdc-notched-outline__notch,
.nav-search-field ::ng-deep .mdc-notched-outline__trailing { border-color: rgba(255,255,255,0.35); }
.nav-search-field ::ng-deep .mat-mdc-text-field-wrapper { background: rgba(255,255,255,0.08); }
.nav-search-field ::ng-deep .mat-mdc-floating-label { color: rgba(255,255,255,0.7); }
.nav-search-field ::ng-deep .mat-mdc-input-element { color: #fff; }
.nav-search-field ::ng-deep .mat-mdc-form-field-icon-suffix mat-icon { color: var(--accent); }

.nav-actions { display: flex; align-items: center; gap: 8px; }
.nav-action { color: #fff !important; }
.nav-action-text { margin-left: 6px; }
.nav-cart {
  background: var(--accent) !important;
  color: var(--accent-ink) !important;
}

.nav-bottom { background: var(--nav-2); color: #fff; }
.nav-bottom-inner {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 0;
}
.pill { color: #fff !important; }
.nav-spacer { flex: 1; }
.nav-note { opacity: 0.8; font-size: 12px; }

.content { padding: 18px 0 32px; }

@media (max-width: 820px) {
  .nav-action-text { display: none; }
  .nav-actions { gap: 0; }
}
"""

    @staticmethod
    def _customer_component_css() -> str:
        return """.storefront { margin-top: 12px; }

.storefront-shell {
  background: transparent;
}

.page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.searchbar {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  flex-wrap: wrap;
}

.searchbar-field { flex: 1; min-width: 260px; }
.searchbar-actions { display: flex; gap: 10px; flex-wrap: wrap; }

.hero {
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
  gap: 18px;
  background: linear-gradient(135deg, rgba(254,189,105,0.25), rgba(10,103,255,0.10));
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 18px;
}

.hero-kicker { color: var(--muted); font-weight: 600; letter-spacing: 0.3px; }
.hero-title { margin: 6px 0 6px; font-size: 22px; }
.hero-subtitle { margin: 0; color: var(--muted); max-width: 60ch; }
.hero-cta { margin-top: 12px; display: flex; gap: 10px; flex-wrap: wrap; }

.hero-art {
  border-radius: calc(var(--radius) - 4px);
  background: rgba(255,255,255,0.7);
  border: 1px solid var(--border);
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.hero-badge {
  display: inline-flex;
  gap: 8px;
  align-items: center;
  font-weight: 700;
}
.hero-metrics {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}
.metric {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 10px;
}
.metric-value { font-weight: 800; }
.metric-label { color: var(--muted); font-size: 12px; margin-top: 2px; }

.loading {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 18px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
}
.loading-text { color: var(--muted); }

.empty {
  border-radius: var(--radius);
  border: 1px solid var(--border);
}
.empty-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  background: rgba(19,25,33,0.06);
  margin-bottom: 10px;
}
.empty-title { font-weight: 800; font-size: 18px; }
.empty-subtitle { margin-top: 4px; color: var(--muted); }
.empty-actions { margin-top: 12px; display: flex; gap: 10px; flex-wrap: wrap; }

.grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.card {
  border-radius: var(--radius);
  border: 1px solid var(--border);
  overflow: hidden;
}
.avatar {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, rgba(10,103,255,0.25), rgba(254,189,105,0.35));
  font-weight: 800;
  color: var(--ink);
}
.card-title { font-weight: 800; }
.card-subtitle { color: var(--muted); }

.card-content { padding-top: 8px; }
.meta {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--muted);
  margin: 6px 0;
}
.meta mat-icon { font-size: 18px; width: 18px; height: 18px; }
.truncate { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.card-actions { padding: 0 8px 10px; }

.sidepanel { width: min(420px, 92vw); padding: 0; }
.sidepanel-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 16px;
  border-bottom: 1px solid var(--border);
}
.sidepanel-title .title { font-weight: 900; font-size: 16px; }
.sidepanel-title .subtitle { color: var(--muted); font-size: 12px; margin-top: 2px; }
.sidepanel-form { padding: 16px; display: flex; flex-direction: column; gap: 10px; }
.sidepanel-actions { display: flex; justify-content: flex-end; gap: 10px; padding-top: 6px; }

@media (max-width: 1100px) {
  .grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}
@media (max-width: 820px) {
  .hero { grid-template-columns: 1fr; }
  .grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 520px) {
  .grid { grid-template-columns: 1fr; }
}
"""

    @staticmethod
    def _customers_module_ts() -> str:
        return """import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClientModule } from '@angular/common/http';
import { ReactiveFormsModule } from '@angular/forms';

// Angular Material
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatMenuModule } from '@angular/material/menu';
import { MatPaginatorModule } from '@angular/material/paginator';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { MatSortModule } from '@angular/material/sort';
import { MatTableModule } from '@angular/material/table';

import { CustomerListComponent } from './components/customer-list.component';

@NgModule({
  declarations: [CustomerListComponent],
  imports: [
    CommonModule,
    HttpClientModule,
    ReactiveFormsModule,
    MatButtonModule,
    MatCardModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatMenuModule,
    MatPaginatorModule,
    MatProgressSpinnerModule,
    MatSidenavModule,
    MatSnackBarModule,
    MatSortModule,
    MatTableModule
  ],
  exports: [CustomerListComponent]
})
export class CustomersModule {}
"""

    @staticmethod
    def _nginx_conf() -> str:
        return """server {
  listen 80;
  server_name _;
  root /usr/share/nginx/html;
  index index.html;

  location / {
    try_files $uri $uri/ /index.html;
  }
}
"""
