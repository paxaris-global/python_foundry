from app.services.generators.base import BaseGenerator
from app.services.templates.jinja_renderer import JinjaRenderer
from app.services.templates.template_registry import TemplateRegistry


class AngularGenerator(BaseGenerator):
    def __init__(self) -> None:
        self.renderer = JinjaRenderer()

    def generate(self, project_spec: dict, api_contract: dict, rag_context: list[dict]) -> dict[str, str]:
        app_name = project_spec["project_name"]
        frontend_spec = project_spec.get("frontend", {})
        ui_profile = frontend_spec.get("ui_profile", "professional")
        layout_style = frontend_spec.get("layout_style", "workspace")
        theme_tokens = frontend_spec.get("theme_tokens", {})
        app_title = self._title_case(app_name)

        # Build design_hints from domain, features and ui_profile so templates never get UndefinedError
        domain = project_spec.get("domain", "")
        features = project_spec.get("features", [])
        design_hints: list[str] = []
        if ui_profile in ("luxury", "premium"):
            design_hints.append("luxury")
        if ui_profile in ("minimal", "clean"):
            design_hints.append("minimal")
        if ui_profile in ("corporate", "enterprise"):
            design_hints.append("corporate")
        if domain in ("ecommerce", "retail"):
            design_hints.append("colorful")
        if "dark" in features or "dark_mode" in features:
            design_hints.append("dark")
        if not design_hints:
            design_hints.append("professional")

        ctx = {
            "project_name": app_name,
            "api_base_url": "http://localhost:8080",
            "ui_profile": ui_profile,
            "layout_style": layout_style,
            "theme_tokens": theme_tokens,
            "design_hints": design_hints,
            "domain": domain,
            "features": features,
            "app_title": app_title,
            "year": "2026",
            "error": "",
            "production": False,
        }

        files: dict[str, str] = {
            "frontend/package.json": self.renderer.render(TemplateRegistry.ANGULAR_PACKAGE_JSON.path, ctx),
            "frontend/angular.json": self.renderer.render(TemplateRegistry.ANGULAR_ANGULAR_JSON.path, ctx),
            "frontend/tsconfig.json": self._tsconfig_json(),
            "frontend/tsconfig.app.json": self._tsconfig_app_json(),
            "frontend/.gitignore": self._gitignore(),
            "frontend/src/main.ts": self._main_ts(),
            "frontend/src/index.html": self._index_html(app_title, ui_profile),
            "frontend/src/styles.css": self.renderer.render(TemplateRegistry.ANGULAR_STYLES_CSS.path, ctx),
            "frontend/src/app/app.module.ts": self.renderer.render(TemplateRegistry.ANGULAR_APP_MODULE.path, ctx),
            "frontend/src/app/app-routing.module.ts": self.renderer.render(TemplateRegistry.ANGULAR_APP_ROUTING.path, ctx),
            "frontend/src/app/app.component.ts": self._app_component_ts(app_title, ui_profile, layout_style),
            "frontend/src/app/app.component.html": self._app_component_html(app_title, layout_style),
            "frontend/src/app/app.component.css": self._app_component_css(theme_tokens, layout_style),
            "frontend/src/app/core/services/api.service.ts": self.renderer.render(TemplateRegistry.ANGULAR_SERVICE.path, ctx),
            "frontend/src/app/features/customers/components/customer-list.component.ts": self.renderer.render(
                TemplateRegistry.ANGULAR_COMPONENT.path,
                ctx,
            ),
            "frontend/src/app/features/customers/components/customer-list.component.html": self.renderer.render(
              TemplateRegistry.ANGULAR_COMPONENT_HTML.path,
              ctx,
            ),
            "frontend/src/app/features/customers/components/customer-list.component.css": self.renderer.render(
              TemplateRegistry.ANGULAR_COMPONENT_CSS.path,
              ctx,
            ),
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
    def _title_case(value: str) -> str:
        return " ".join(part.capitalize() for part in value.replace("_", "-").split("-") if part) or "Generated App"

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
    def _index_html(app_name: str, ui_profile: str) -> str:
        return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <title>{app_name}</title>
  <base href=\"/\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <meta name=\"description\" content=\"{app_name} - {ui_profile} full-stack workspace generated by AI\">
  <link rel=\"preconnect\" href=\"https://fonts.googleapis.com\">
  <link rel=\"preconnect\" href=\"https://fonts.gstatic.com\" crossorigin>
  <link href=\"https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap\" rel=\"stylesheet\">
</head>
<body>
  <app-root></app-root>
</body>
</html>
"""


    @staticmethod
    def _app_component_ts(app_name: str, ui_profile: str, layout_style: str) -> str:
        return f"""import {{ Component }} from '@angular/core';

@Component({{
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
}})
export class AppComponent {{
  readonly title = '{app_name}';
  readonly subtitle = 'A {ui_profile} {layout_style} experience generated with Angular + Spring Boot';
  readonly navigation = [
    {{ label: 'Customers', icon: 'groups', route: '/customers', disabled: false }},
    {{ label: 'Dashboard', icon: 'dashboard', route: '/customers', disabled: true }},
    {{ label: 'Reports', icon: 'analytics', route: '/customers', disabled: true }}
  ];
  readonly quickStats = [
    {{ label: 'Uptime', value: '99.95%' }},
    {{ label: 'Response', value: '180ms' }},
    {{ label: 'Automation', value: 'Enabled' }}
  ];
}}
"""

    @staticmethod
    def _app_component_html(app_name: str, layout_style: str) -> str:
        return f"""<main class=\"app-shell {layout_style}\">
  <header class=\"topbar\">
    <div>
      <h1>{{{{ title }}}}</h1>
      <p>{{{{ subtitle }}}}</p>
    </div>
    <button mat-raised-button color=\"primary\">Launch Workflow</button>
  </header>

  <div class=\"shell-body\">
    <aside class=\"nav-panel\">
      <a
        *ngFor=\"let item of navigation\"
        mat-stroked-button
        [routerLink]=\"item.disabled ? null : item.route\"
        [disabled]=\"item.disabled\"
      >
        <mat-icon>{{{{ item.icon }}}}</mat-icon>
        <span>{{{{ item.label }}}}</span>
      </a>
    </aside>

    <section class=\"shell-content\">
      <section class=\"hero\">
        <h2>{app_name}</h2>
        <p>This UI shell is intentionally polished to give your generated project a professional starting point.</p>
        <div class=\"stats\">
          <article class=\"stat\" *ngFor=\"let stat of quickStats\">
            <strong>{{{{ stat.value }}}}</strong>
            <span>{{{{ stat.label }}}}</span>
          </article>
        </div>
      </section>

      <section class=\"surface\">
        <router-outlet></router-outlet>
      </section>
    </section>
  </div>
</main>
"""

    @staticmethod
    def _app_component_css(theme_tokens: dict, layout_style: str) -> str:
        primary = theme_tokens.get("primary", "#2563eb")
        accent = theme_tokens.get("accent", "#14b8a6")
        surface = theme_tokens.get("surface", "#ffffff")
        text = theme_tokens.get("text", "#0f172a")
        muted = theme_tokens.get("muted", "#475569")
        css = """/* layout profile: __LAYOUT_STYLE__ */
:host {
  --pf-primary: __PRIMARY__;
  --pf-accent: __ACCENT__;
  --pf-surface: __SURFACE__;
  --pf-text: __TEXT__;
  --pf-muted: __MUTED__;
}

.app-shell {
  color: var(--pf-text);
  max-width: 1240px;
  margin: 0 auto;
  padding: 1.5rem;
}

.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.25rem;
}

.topbar h1 {
  margin: 0;
  font-size: 1.8rem;
}

.topbar p {
  margin: 0.35rem 0 0;
  color: var(--pf-muted);
}

.shell-body {
  display: grid;
  grid-template-columns: 240px 1fr;
  gap: 1rem;
}

.nav-panel {
  background: color-mix(in srgb, var(--pf-primary) 8%, var(--pf-surface));
  border: 1px solid color-mix(in srgb, var(--pf-primary) 18%, white);
  border-radius: 16px;
  padding: 1rem;
  display: grid;
  gap: 0.65rem;
  height: fit-content;
}

.nav-panel a {
  justify-content: flex-start;
  gap: 0.5rem;
}

.shell-content {
  display: grid;
  gap: 1rem;
}

.hero {
  border-radius: 18px;
  padding: 1.4rem;
  color: #fff;
  background: linear-gradient(135deg, var(--pf-primary) 0%, var(--pf-accent) 100%);
}

.hero h2 {
  margin: 0;
}

.hero p {
  margin: 0.5rem 0 1rem;
  opacity: 0.95;
}

.stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 0.75rem;
}

.stat {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.35);
  border-radius: 12px;
  padding: 0.75rem;
}

.stat strong {
  display: block;
  font-size: 1.1rem;
}

.surface {
  background: var(--pf-surface);
  border: 1px solid color-mix(in srgb, var(--pf-primary) 16%, #dbeafe);
  border-radius: 16px;
  padding: 1rem;
  box-shadow: 0 16px 32px rgba(15, 23, 42, 0.08);
}

.app-shell.landing .shell-body {
  grid-template-columns: 1fr;
}

.app-shell.landing .nav-panel {
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
}

@media (max-width: 980px) {
  .shell-body {
    grid-template-columns: 1fr;
  }
}
"""
        return (
            css.replace("__LAYOUT_STYLE__", layout_style)
            .replace("__PRIMARY__", primary)
            .replace("__ACCENT__", accent)
            .replace("__SURFACE__", surface)
            .replace("__TEXT__", text)
            .replace("__MUTED__", muted)
        )


    @staticmethod
    def _customers_module_ts() -> str:
        return """import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { CustomerListComponent } from './components/customer-list.component';

@NgModule({
  declarations: [CustomerListComponent],
  imports: [CommonModule, HttpClientModule, FormsModule],
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
