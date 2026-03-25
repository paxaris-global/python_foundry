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
        }

        files: dict[str, str] = {
            "frontend/package.json": self.renderer.render(TemplateRegistry.ANGULAR_PACKAGE_JSON.path, ctx),
            "frontend/angular.json": self.renderer.render(TemplateRegistry.ANGULAR_ANGULAR_JSON.path, ctx),
            "frontend/tsconfig.json": self._tsconfig_json(),
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
        }
        return files

    @staticmethod
    def _tsconfig_json() -> str:
        return """{
  \"compileOnSave\": false,
  \"compilerOptions\": {
    \"baseUrl\": \"./\",
    \"outDir\": \"./dist/out-tsc\",
    \"forceConsistentCasingInFileNames\": true,
    \"strict\": true,
    \"noImplicitOverride\": true,
    \"noPropertyAccessFromIndexSignature\": true,
    \"noImplicitReturns\": true,
    \"noFallthroughCasesInSwitch\": true,
    \"sourceMap\": true,
    \"declaration\": false,
    \"downlevelIteration\": true,
    \"experimentalDecorators\": true,
    \"moduleResolution\": \"node\",
    \"importHelpers\": true,
    \"target\": \"ES2022\",
    \"module\": \"ES2022\",
    \"lib\": [\"ES2022\", \"dom\"]
  }
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
  --bg: #f8fbf9;
  --ink: #152018;
  --brand: #1b8f5a;
  --brand-ink: #ffffff;
}

html, body {
  margin: 0;
  font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
  background: radial-gradient(circle at top left, #ffffff 0%, var(--bg) 60%);
  color: var(--ink);
}

* {
  box-sizing: border-box;
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
  title = 'AI Generated CRM';
}
"""

    @staticmethod
    def _app_component_html(app_name: str) -> str:
        return f"""<main class=\"layout\">
  <header>
    <h1>{app_name}</h1>
    <p>Generated full-stack workspace with Angular + Spring Boot</p>
  </header>

  <section class=\"surface\">
    <router-outlet></router-outlet>
  </section>
</main>
"""

    @staticmethod
    def _app_component_css() -> str:
        return """.layout {
  max-width: 980px;
  margin: 0 auto;
  padding: 2rem 1rem;
}

header h1 {
  margin-bottom: 0.3rem;
}

.surface {
  background: white;
  border: 1px solid #d6e4dc;
  border-radius: 12px;
  padding: 1rem;
}
"""

    @staticmethod
    def _customer_component_css() -> str:
        return """h2 {
  margin-top: 0;
}
"""

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
