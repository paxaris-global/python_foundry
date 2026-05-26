import re

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
            "api_base_url": "http://localhost:18080",
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
            "frontend/src/app/app.component.ts": self._app_component_ts(app_title, ui_profile, layout_style, domain),
            "frontend/src/app/app.component.html": self._app_component_html(app_title, layout_style, domain),
            "frontend/src/app/app.component.css": self._app_component_css(theme_tokens, layout_style, domain),
            "frontend/src/app/core/services/api.service.ts": self._api_service_from_contract(api_contract),
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
              {"production": False, "api_base_url": "http://localhost:18080/api/v1"},
            ),
            "frontend/src/environments/environment.prod.ts": self.renderer.render(
              TemplateRegistry.ANGULAR_ENVIRONMENT.path,
              {"production": True, "api_base_url": "/api/v1"},
            ),
            "frontend/nginx.conf": self._nginx_conf(),
            "frontend/Dockerfile": self.renderer.render(TemplateRegistry.ANGULAR_DOCKERFILE.path, ctx),
        }
        if domain in {"ecommerce", "retail"}:
            files["frontend/src/styles.css"] = (
                files["frontend/src/styles.css"].rstrip() + "\n\n" + self._ecommerce_global_css(theme_tokens)
            )
            files["frontend/src/app/app.module.ts"] = self._ecommerce_app_module_ts()
            files["frontend/src/app/app-routing.module.ts"] = self._ecommerce_app_routing_ts()
            files["frontend/src/app/app.component.ts"] = self._ecommerce_app_component_ts(app_title)
            files["frontend/src/app/app.component.html"] = self._ecommerce_app_component_html(app_title)
            files["frontend/src/app/app.component.css"] = self._ecommerce_app_component_css(theme_tokens)
            files["frontend/src/app/features/home/components/home.component.ts"] = (
                self._ecommerce_home_component_ts(app_title)
            )
            files["frontend/src/app/features/home/components/home.component.html"] = (
                self._ecommerce_home_component_html()
            )
            files["frontend/src/app/features/home/components/home.component.css"] = (
                self._ecommerce_home_component_css(theme_tokens)
            )
            files["frontend/src/app/features/home/home.module.ts"] = self._ecommerce_home_module_ts()
            files["frontend/src/app/features/catalog/components/product-list.component.ts"] = (
                self._ecommerce_product_list_component_ts()
            )
            files["frontend/src/app/features/catalog/components/product-list.component.html"] = (
                self._ecommerce_product_list_component_html()
            )
            files["frontend/src/app/features/catalog/components/product-list.component.css"] = (
                self._ecommerce_product_list_component_css(theme_tokens)
            )
            files["frontend/src/app/features/catalog/components/product-detail.component.ts"] = (
                self._ecommerce_product_detail_component_ts()
            )
            files["frontend/src/app/features/catalog/components/product-detail.component.html"] = (
                self._ecommerce_product_detail_component_html()
            )
            files["frontend/src/app/features/catalog/components/product-detail.component.css"] = (
                self._ecommerce_product_detail_component_css(theme_tokens)
            )
            files["frontend/src/app/features/catalog/catalog.module.ts"] = self._ecommerce_catalog_module_ts()
            files["frontend/src/app/core/services/cart.service.ts"] = self._ecommerce_cart_service_ts()
            for page in ["cart", "login", "signup", "checkout", "wishlist", "account", "admin"]:
                files[f"frontend/src/app/features/experience/components/{page}.component.ts"] = (
                    self._ecommerce_experience_component_ts(page)
                )
                files[f"frontend/src/app/features/experience/components/{page}.component.html"] = (
                    self._ecommerce_experience_component_html(page)
                )
                files[f"frontend/src/app/features/experience/components/{page}.component.css"] = (
                    self._ecommerce_experience_component_css(page)
                )
        return files

    @staticmethod
    def _api_service_from_contract(api_contract: dict) -> str:
        paths = api_contract.get("paths", {})
        has_products = any("/products" in p for p in paths.keys())
        customer_block = """export interface Customer {
  id: string;
  name: string;
  email: string;
  company: string;
  phone?: string;
  address?: string;
}
"""
        product_interface = """
export interface Product {
  id: string;
  name: string;
  description?: string;
  brand?: string;
  category?: string;
  imageUrl?: string;
  price: number;
  stockQuantity?: number;
}
""" if has_products else ""
        product_methods = """
  getProducts(): Observable<Product[]> {
    return this.http.get<Product[]>(`${this.baseUrl}/products`);
  }

  getProductById(id: string): Observable<Product> {
    return this.http.get<Product>(`${this.baseUrl}/products/${id}`);
  }

  createProduct(product: Omit<Product, 'id'>): Observable<Product> {
    return this.http.post<Product>(`${this.baseUrl}/products`, product);
  }

  updateProduct(id: string, product: Partial<Omit<Product, 'id'>>): Observable<Product> {
    return this.http.put<Product>(`${this.baseUrl}/products/${id}`, product);
  }

  deleteProduct(id: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/products/${id}`);
  }
""" if has_products else ""
        # Normalize accidental double slashes from base URL composition.
        result = f"""import {{ Injectable }} from '@angular/core';
import {{ HttpClient }} from '@angular/common/http';
import {{ Observable }} from 'rxjs';
import {{ environment }} from '../../../environments/environment';

{customer_block}{product_interface}
@Injectable({{
  providedIn: 'root'
}})
export class ApiService {{
  private readonly baseUrl = environment.apiBaseUrl.replace(/\\/$/, '');

  constructor(private http: HttpClient) {{}}

  getCustomers(): Observable<Customer[]> {{
    return this.http.get<Customer[]>(`${{this.baseUrl}}/customers`);
  }}

  getCustomerById(id: string): Observable<Customer> {{
    return this.http.get<Customer>(`${{this.baseUrl}}/customers/${{id}}`);
  }}

  createCustomer(customer: Omit<Customer, 'id'>): Observable<Customer> {{
    return this.http.post<Customer>(`${{this.baseUrl}}/customers`, customer);
  }}

  updateCustomer(id: string, customer: Partial<Omit<Customer, 'id'>>): Observable<Customer> {{
    return this.http.put<Customer>(`${{this.baseUrl}}/customers/${{id}}`, customer);
  }}

  deleteCustomer(id: string): Observable<void> {{
    return this.http.delete<void>(`${{this.baseUrl}}/customers/${{id}}`);
  }}
{product_methods}
}}
"""
        return re.sub(r"\n{3,}", "\n\n", result).rstrip() + "\n"

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
        return """name: Build Push And GitOps Update (Frontend)

on:
  push:
    branches:
      - main
      - master

permissions:
  contents: write

jobs:
  build-and-update:
    if: github.actor != 'github-actions[bot]'
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set image variables
        id: vars
        run: |
          IMAGE_REPO="devopspaxarisglobalrepo/finaltest36-admin-backend-test-frontend"
          IMAGE_TAG="${GITHUB_SHA}"
          echo "image_repo=$IMAGE_REPO" >> "$GITHUB_OUTPUT"
          echo "image_tag=$IMAGE_TAG" >> "$GITHUB_OUTPUT"

      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ vars.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Set up QEMU
        uses: docker/setup-qemu-action@v3

      - name: Build and push image
        uses: docker/build-push-action@v6
        with:
          context: ./frontend
          file: ./frontend/Dockerfile
          platforms: linux/amd64,linux/arm64
          push: true
          tags: |
            ${{ steps.vars.outputs.image_repo }}:latest
            ${{ steps.vars.outputs.image_repo }}:${{ steps.vars.outputs.image_tag }}

      - name: Update k8 image tag
        run: |
          sed -E -i.bak "s|^([[:space:]]*)image:[[:space:]].*|\\1image: ${{ steps.vars.outputs.image_repo }}:${{ steps.vars.outputs.image_tag }}|" k8/deployment.yaml
          rm -f k8/deployment.yaml.bak

      - name: Commit and push manifest changes
        run: |
          if git diff --quiet; then
            echo "No manifest changes to commit"
            exit 0
          fi
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add k8/deployment.yaml
          git commit -m "ci: update image tag [skip ci]"
          git push
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
    def _app_component_ts(app_name: str, ui_profile: str, layout_style: str, domain: str) -> str:
        return f"""import {{ Component }} from '@angular/core';

@Component({{
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
}})
export class AppComponent {{
  readonly title = '{app_name}';
  readonly subtitle = 'A {ui_profile} {layout_style} {domain} experience generated with Angular + Spring Boot';
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
    def _app_component_html(app_name: str, layout_style: str, domain: str) -> str:
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
        <p>This {domain} UI shell is intentionally polished to give your generated project a professional starting point.</p>
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
    def _app_component_css(theme_tokens: dict, layout_style: str, domain: str) -> str:
        primary = theme_tokens.get("primary", "#2563eb")
        accent = theme_tokens.get("accent", "#14b8a6")
        surface = theme_tokens.get("surface", "#ffffff")
        text = theme_tokens.get("text", "#0f172a")
        muted = theme_tokens.get("muted", "#475569")
        css = """/* layout profile: __LAYOUT_STYLE__ | domain: __DOMAIN__ */
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
            .replace("__DOMAIN__", domain)
            .replace("__PRIMARY__", primary)
            .replace("__ACCENT__", accent)
            .replace("__SURFACE__", surface)
            .replace("__TEXT__", text)
            .replace("__MUTED__", muted)
        )

    @staticmethod
    def _ecommerce_app_component_ts(app_name: str) -> str:
        return f"""import {{ Component }} from '@angular/core';
import {{ CartService }} from './core/services/cart.service';

@Component({{
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
}})
export class AppComponent {{
  readonly title = '{app_name}';
  readonly promo = 'Color Rush Sale | Futuristic fashion edits live now | Free shipping over $49';
  readonly topCategories = ['Men', 'Women', 'Kids', 'Beauty', 'Footwear', 'Deals'];
  readonly megaMenu: Record<string, string[]> = {{
    Men: ['T-Shirts', 'Shirts', 'Jeans', 'Footwear', 'Watches', 'Sportswear'],
    Women: ['Dresses', 'Tops', 'Kurtas', 'Heels', 'Handbags', 'Jewellery'],
    Kids: ['Boys Clothing', 'Girls Clothing', 'Infantwear', 'Toys', 'School'],
    Beauty: ['Makeup', 'Skincare', 'Haircare', 'Fragrances', 'Grooming'],
    Footwear: ['Sneakers', 'Heels', 'Boots', 'Slides', 'Running'],
    Deals: ['Flash Sale', 'Clearance', 'New Offers', 'Bundle Deals'],
  }};
  activeMegaMenu: string | null = null;
  cartCount = 0;

  constructor(private cartService: CartService) {{
    this.cartService.items$.subscribe(items => {{
      this.cartCount = items.reduce((total, item) => total + item.quantity, 0);
    }});
  }}

  openMegaMenu(category: string): void {{
    this.activeMegaMenu = category;
  }}

  closeMegaMenu(): void {{
    this.activeMegaMenu = null;
  }}
}}
"""

    @staticmethod
    def _ecommerce_app_component_html(app_name: str) -> str:
        return f"""<div class=\"promo-strip\">{{{{ promo }}}}</div>
<header class=\"main-nav\">
  <a class=\"brand\" [routerLink]=\"['/']\">{app_name}<span>Studio</span></a>
  <nav class=\"category-nav\" (mouseleave)=\"closeMegaMenu()\">
    <a *ngFor=\"let cat of topCategories\" [routerLink]=\"['/products']\" [queryParams]=\"{{ category: cat.toLowerCase() }}\" (mouseenter)=\"openMegaMenu(cat)\">{{{{ cat }}}}</a>
  </nav>
  <div class=\"actions\">
    <input class=\"search\" placeholder=\"Search for products, brands and more\" />
    <a class=\"nav-link\" [routerLink]=\"['/auth/login']\">Login</a>
    <a class=\"nav-link signup\" [routerLink]=\"['/auth/signup']\">Signup</a>
    <a class=\"icon-btn\" [routerLink]=\"['/account']\" aria-label=\"Profile\">👤</a>
    <a class=\"icon-btn\" [routerLink]=\"['/wishlist']\" aria-label=\"Wishlist\">♡</a>
    <a class=\"icon-btn cart-button\" [routerLink]=\"['/cart']\" aria-label=\"Cart\">🛍<span>{{{{ cartCount }}}}</span></a>
  </div>
</header>
<section class=\"mega-menu\" *ngIf=\"activeMegaMenu\" (mouseleave)=\"closeMegaMenu()\">
  <h4>{{{{ activeMegaMenu }}}}</h4>
  <div class=\"mega-items\">
    <a *ngFor=\"let item of megaMenu[activeMegaMenu]\" [routerLink]=\"['/products']\">{{{{ item }}}}</a>
  </div>
</section>

<main class=\"shell-content\">
  <section class=\"quick-links\">
    <a [routerLink]=\"['/']\">Home</a>
    <a [routerLink]=\"['/products']\">Products</a>
    <a [routerLink]=\"['/cart']\">Cart</a>
    <a [routerLink]=\"['/checkout']\">Checkout</a>
    <a [routerLink]=\"['/admin']\">Admin</a>
  </section>
  <router-outlet></router-outlet>
</main>
"""

    @staticmethod
    def _ecommerce_app_component_css(theme_tokens: dict) -> str:
        primary = theme_tokens.get("primary", "#ff3f6c")
        accent = theme_tokens.get("accent", "#ff6b6b")
        surface = theme_tokens.get("surface", "#ffffff")
        text = theme_tokens.get("text", "#1f2937")
        muted = theme_tokens.get("muted", "#6b7280")
        return f""":host {{
  --brand-primary: {primary};
  --brand-accent: {accent};
  --surface: {surface};
  --text: {text};
  --muted: {muted};
  display: block;
  background:
    radial-gradient(circle at 12% 8%, rgba(255,63,108,.22), transparent 28%),
    radial-gradient(circle at 92% 12%, rgba(124,58,237,.18), transparent 30%),
    linear-gradient(135deg, #fff7fb 0%, #eef5ff 45%, #fffaf0 100%);
  color: var(--text);
  min-height: 100vh;
  font-family: Inter, sans-serif;
}}
.promo-strip {{
  text-align: center;
  padding: 8px 12px;
  background: linear-gradient(90deg, var(--brand-primary), var(--brand-accent));
  color: #fff;
  font-weight: 600;
  letter-spacing: 0.2px;
}}
.main-nav {{
  position: sticky;
  top: 0;
  z-index: 1000;
  display: grid;
  grid-template-columns: 160px 1fr auto;
  gap: 16px;
  align-items: center;
  background: rgba(255,255,255,.82);
  border-bottom: 1px solid rgba(255,255,255,.62);
  padding: 14px 20px;
  backdrop-filter: blur(18px);
  box-shadow: 0 18px 45px rgba(15,23,42,.08);
}}
.brand {{
  color: var(--text);
  text-decoration: none;
  font-size: 1.35rem;
  font-weight: 900;
  letter-spacing: 0.4px;
}}
.brand span {{
  margin-left: 4px;
  background: linear-gradient(90deg, var(--brand-primary), #7c3aed, var(--brand-accent));
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}}
.category-nav {{
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
}}
.category-nav a {{
  text-decoration: none;
  color: var(--text);
  font-weight: 600;
  font-size: 0.88rem;
}}
.actions {{
  display: flex;
  align-items: center;
  gap: 8px;
}}
.search {{
  width: 320px;
  border: 1px solid #d8dee8;
  border-radius: 999px;
  padding: 9px 14px;
}}
.icon-btn {{
  border: 1px solid #d8dee8;
  background: #fff;
  border-radius: 999px;
  width: 36px;
  height: 36px;
  cursor: pointer;
  color: var(--text);
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  position: relative;
}}
.nav-link {{
  color: var(--text);
  font-size: .86rem;
  font-weight: 800;
  text-decoration: none;
  padding: 9px 12px;
  border-radius: 999px;
  background: rgba(255,255,255,.72);
  border: 1px solid rgba(216,222,232,.8);
}}
.nav-link.signup {{
  color: #fff;
  border: 0;
  background: linear-gradient(135deg, var(--brand-primary), #7c3aed);
  box-shadow: 0 12px 24px rgba(255,63,108,.22);
}}
.cart-button span {{
  position: absolute;
  top: -7px;
  right: -7px;
  min-width: 18px;
  height: 18px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: linear-gradient(135deg, #22c55e, #14b8a6);
  color: #fff;
  font-size: .68rem;
  font-weight: 900;
}}
.mega-menu {{
  position: sticky;
  top: 68px;
  z-index: 1100;
  background: #fff;
  border-bottom: 1px solid #eceff3;
  padding: 12px 20px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
}}
.mega-menu h4 {{
  margin: 0 0 8px;
}}
.mega-items {{
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 8px;
}}
.mega-items a {{
  text-decoration: none;
  color: #374151;
  font-weight: 600;
  padding: 8px;
  border-radius: 8px;
}}
.mega-items a:hover {{
  background: #f3f4f6;
}}
.shell-content {{
  max-width: 1240px;
  margin: 0 auto;
  padding: 16px;
}}
.quick-links {{
  display: flex;
  gap: 10px;
  margin-bottom: 12px;
}}
.quick-links a {{
  text-decoration: none;
  border: 1px solid #d8dee8;
  border-radius: 999px;
  padding: 7px 12px;
  background: #fff;
  color: #111827;
  font-weight: 700;
}}
@media (max-width: 1024px) {{
  .main-nav {{
    grid-template-columns: 1fr;
  }}
  .search {{ width: 100%; }}
  .mega-menu {{
    top: 118px;
  }}
  .mega-items {{
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }}
}}
@media (max-width: 640px) {{
  .mega-items {{
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }}
}}
"""

    @staticmethod
    def _ecommerce_home_component_ts(app_name: str) -> str:
        return f"""import {{ Component }} from '@angular/core';

@Component({{
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css']
}})
export class HomeComponent {{
  readonly title = '{app_name}';
  readonly deals = [
    {{ title: 'Minimum 40% OFF', subtitle: 'Ethnicwear Picks', img: 'https://picsum.photos/seed/deal1/500/300' }},
    {{ title: 'Sneaker Fest', subtitle: 'Top brands from $49', img: 'https://picsum.photos/seed/deal2/500/300' }},
    {{ title: 'Beauty Bonanza', subtitle: 'Buy 2 Get 1', img: 'https://picsum.photos/seed/deal3/500/300' }},
  ];
  readonly banners = [
    {{ title: 'Streetwear Drop', subtitle: 'Up to 60% OFF', cta: 'Shop Men' }},
    {{ title: 'Style Refresh', subtitle: 'Curated looks for Women', cta: 'Shop Women' }},
    {{ title: 'Beauty Picks', subtitle: 'Top brands this week', cta: 'Shop Beauty' }},
  ];
  readonly chips = ['Summer Edit', 'New Arrivals', 'Trending', 'Ethnic', 'Sneakers', 'Beauty Deals'];
  readonly featured = [
    {{ label: 'Topwear', img: 'https://picsum.photos/seed/topwear/480/320' }},
    {{ label: 'Footwear', img: 'https://picsum.photos/seed/footwear/480/320' }},
    {{ label: 'Watches', img: 'https://picsum.photos/seed/watches/480/320' }},
    {{ label: 'Home Decor', img: 'https://picsum.photos/seed/home/480/320' }},
  ];
  readonly shopByCategory = [
    'Casual Shirts', 'Dresses', 'Sports Shoes', 'Watches', 'Handbags', 'Skincare', 'Kurta Sets', 'Home Decor'
  ];
  readonly featuredBrands = ['Roadster', 'H&M', 'Puma', 'Levis', 'ONLY', 'Fossil', 'Libas', 'Nike'];
}}
"""

    @staticmethod
    def _ecommerce_home_component_html() -> str:
        return """<section class=\"deals\">
  <article class=\"deal-card\" *ngFor=\"let deal of deals\">
    <img [src]=\"deal.img\" [alt]=\"deal.title\" />
    <div class=\"deal-overlay\">
      <p>{{ deal.subtitle }}</p>
      <h3>{{ deal.title }}</h3>
    </div>
  </article>
</section>

<section class=\"hero-grid\">
  <article class=\"hero-card\" *ngFor=\"let banner of banners\">
    <p>{{ banner.subtitle }}</p>
    <h2>{{ banner.title }}</h2>
    <button>{{ banner.cta }}</button>
  </article>
</section>

<section class=\"chips\">
  <button *ngFor=\"let chip of chips\">{{ chip }}</button>
</section>

<section class=\"featured\">
  <article class=\"featured-card\" *ngFor=\"let item of featured\">
    <img [src]=\"item.img\" [alt]=\"item.label\" />
    <h3>{{ item.label }}</h3>
  </article>
</section>

<section class=\"category-section\">
  <h2>Shop by Category</h2>
  <div class=\"category-grid\">
    <a *ngFor=\"let c of shopByCategory\" [routerLink]=\"['/products']\">{{ c }}</a>
  </div>
</section>

<section class=\"brands-section\">
  <h2>Featured Brands</h2>
  <div class=\"brand-pills\">
    <span *ngFor=\"let b of featuredBrands\">{{ b }}</span>
  </div>
</section>

<section class=\"catalog-shell\">
  <h2>Trending Products</h2>
  <a class=\"browse-link\" [routerLink]=\"['/products']\">Browse Full Collection</a>
</section>
"""

    @staticmethod
    def _ecommerce_home_component_css(theme_tokens: dict) -> str:
        primary = theme_tokens.get("primary", "#ff3f6c")
        accent = theme_tokens.get("accent", "#ff6b6b")
        return f""":host {{
  display: grid;
  gap: 18px;
}}
.hero-grid {{
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}}
.deals {{
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}}
.deal-card {{
  position: relative;
  border-radius: 14px;
  overflow: hidden;
  min-height: 180px;
}}
.deal-card img {{
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}}
.deal-overlay {{
  position: absolute;
  inset: auto 0 0;
  background: linear-gradient(180deg, transparent, rgba(0,0,0,.72));
  color: #fff;
  padding: 12px;
}}
.deal-overlay p, .deal-overlay h3 {{
  margin: 0;
}}
.hero-card {{
  border-radius: 16px;
  padding: 20px;
  color: #fff;
  background: linear-gradient(135deg, rgba(17,24,39,.82), rgba(99,102,241,.72)), url('https://picsum.photos/seed/fashionhero/800/600') center/cover;
  min-height: 190px;
  display: grid;
  gap: 8px;
  align-content: end;
}}
.hero-card p {{ margin: 0; opacity: .9; }}
.hero-card h2 {{ margin: 0; font-size: 1.4rem; }}
.hero-card button {{
  width: fit-content;
  border: 0;
  border-radius: 999px;
  padding: 9px 14px;
  font-weight: 700;
  cursor: pointer;
}}
.chips {{
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}}
.chips button {{
  border: 1px solid #d8dee8;
  border-radius: 999px;
  background: #fff;
  padding: 8px 12px;
  font-weight: 600;
}}
.featured {{
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}}
.featured-card {{
  border-radius: 14px;
  overflow: hidden;
  background: #fff;
  box-shadow: 0 8px 26px rgba(15,23,42,.07);
}}
.featured-card img {{
  width: 100%;
  height: 160px;
  object-fit: cover;
}}
.featured-card h3 {{
  margin: 10px 12px 14px;
  font-size: 0.95rem;
}}
.catalog-shell {{
  background: #fff;
  border-radius: 16px;
  border: 1px solid #eceff3;
  padding: 16px;
}}
.browse-link {{
  display: inline-block;
  margin-bottom: 12px;
  text-decoration: none;
  font-weight: 700;
  color: var(--brand-primary);
}}
.catalog-shell h2 {{
  margin: 0 0 14px;
}}
.category-section,
.brands-section {{
  background: #fff;
  border: 1px solid #eceff3;
  border-radius: 16px;
  padding: 16px;
}}
.category-section h2,
.brands-section h2 {{
  margin: 0 0 12px;
}}
.category-grid {{
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}}
.category-grid a {{
  text-decoration: none;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 10px;
  text-align: center;
  color: var(--text);
  background: #fafafa;
  font-weight: 600;
}}
.brand-pills {{
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}}
.brand-pills span {{
  border: 1px solid #e5e7eb;
  border-radius: 999px;
  padding: 8px 12px;
  background: #fafafa;
  font-weight: 600;
}}
@media (max-width: 1024px) {{
  .deals {{ grid-template-columns: 1fr; }}
  .hero-grid {{ grid-template-columns: 1fr; }}
  .category-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
  .featured {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
}}
@media (max-width: 640px) {{
  .category-grid {{ grid-template-columns: 1fr; }}
  .featured {{ grid-template-columns: 1fr; }}
}}
"""

    @staticmethod
    def _ecommerce_product_list_component_ts() -> str:
        return """import { Component } from '@angular/core';
import { CartService } from '../../../core/services/cart.service';

interface ProductCard {
  id: number;
  name: string;
  brand: string;
  price: number;
  mrp: number;
  rating: number;
  img: string;
}

@Component({
  selector: 'app-product-list',
  templateUrl: './product-list.component.html',
  styleUrls: ['./product-list.component.css']
})
export class ProductListComponent {
  selectedSort = 'Popularity';
  showFilters = false;
  readonly filters = {
    categories: ['Men', 'Women', 'Footwear', 'Beauty', 'Home'],
    brands: ['Roadster', 'H&M', 'Puma', 'Levis', 'Libas', 'Fossil'],
    sizes: ['XS', 'S', 'M', 'L', 'XL'],
  };
  readonly products: ProductCard[] = [
    { id: 1, name: 'Solid Casual Shirt', brand: 'Roadster', price: 1299, mrp: 2599, rating: 4.3, img: 'https://picsum.photos/seed/prod1/400/520' },
    { id: 2, name: 'Slim Fit Jeans', brand: 'Levis', price: 1899, mrp: 2999, rating: 4.2, img: 'https://picsum.photos/seed/prod2/400/520' },
    { id: 3, name: 'Running Sneakers', brand: 'Puma', price: 2499, mrp: 3999, rating: 4.5, img: 'https://picsum.photos/seed/prod3/400/520' },
    { id: 4, name: 'Printed Kurta Set', brand: 'Libas', price: 1599, mrp: 2799, rating: 4.4, img: 'https://picsum.photos/seed/prod4/400/520' },
    { id: 5, name: 'Classic Wrist Watch', brand: 'Fossil', price: 4999, mrp: 7999, rating: 4.6, img: 'https://picsum.photos/seed/prod5/400/520' },
    { id: 6, name: 'Backpack 24L', brand: 'Wildcraft', price: 1199, mrp: 2199, rating: 4.1, img: 'https://picsum.photos/seed/prod6/400/520' }
  ];

  constructor(private cartService: CartService) {}

  toggleFilters(): void {
    this.showFilters = !this.showFilters;
  }

  addToCart(product: ProductCard): void {
    this.cartService.add(product);
  }
}
"""

    @staticmethod
    def _ecommerce_product_list_component_html() -> str:
        return """<button class=\"mobile-filter-toggle\" (click)=\"toggleFilters()\">Filters</button>
<div class=\"mobile-filter-backdrop\" *ngIf=\"showFilters\" (click)=\"toggleFilters()\"></div>

<section class=\"listing-layout\">
  <aside class=\"filters\" [class.open]=\"showFilters\">
    <button class=\"close-filters\" (click)=\"toggleFilters()\">Close ✕</button>
    <h3>Filters</h3>
    <div class=\"filter-block\">
      <h4>Category</h4>
      <label *ngFor=\"let c of filters.categories\"><input type=\"checkbox\" /> {{ c }}</label>
    </div>
    <div class=\"filter-block\">
      <h4>Brand</h4>
      <label *ngFor=\"let b of filters.brands\"><input type=\"checkbox\" /> {{ b }}</label>
    </div>
    <div class=\"filter-block\">
      <h4>Size</h4>
      <div class=\"size-chips\">
        <span *ngFor=\"let s of filters.sizes\">{{ s }}</span>
      </div>
    </div>
  </aside>

  <section class=\"listing-main\">
    <div class=\"toolbar\">
      <input placeholder=\"Search products\" />
      <select [(ngModel)]=\"selectedSort\">
        <option>Popularity</option>
        <option>Price: Low to High</option>
        <option>Price: High to Low</option>
        <option>Newest</option>
      </select>
    </div>
    <div class=\"product-grid\">
      <article class=\"product-card\" *ngFor=\"let p of products\">
        <a [routerLink]=\"['/product', p.id]\">
          <img [src]=\"p.img\" [alt]=\"p.name\" />
        </a>
        <h3>{{ p.brand }}</h3>
        <p>{{ p.name }}</p>
        <div class=\"price-row\">
          <strong>${{ p.price }}</strong>
          <span class=\"mrp\">${{ p.mrp }}</span>
          <span class=\"rating\">★ {{ p.rating }}</span>
        </div>
        <button (click)="addToCart(p); $event.stopPropagation()">Add to Cart</button>
      </article>
    </div>
  </section>
</section>
"""

    @staticmethod
    def _ecommerce_product_list_component_css(theme_tokens: dict) -> str:
        accent = theme_tokens.get("accent", "#ff6b6b")
        return f""".mobile-filter-toggle {{
  display: none;
}}
.mobile-filter-backdrop {{
  display: none;
}}
.listing-layout {{
  display: grid;
  grid-template-columns: 260px 1fr;
  gap: 14px;
}}
.filters {{
  border: 1px solid #eceff3;
  border-radius: 12px;
  padding: 12px;
  background: #fff;
  height: fit-content;
}}
.close-filters {{
  display: none;
}}
.filters h3 {{
  margin: 0 0 12px;
}}
.filter-block {{
  margin-bottom: 12px;
}}
.filter-block h4 {{
  margin: 0 0 8px;
  font-size: .92rem;
}}
.filter-block label {{
  display: block;
  margin-bottom: 6px;
  font-size: .88rem;
}}
.size-chips {{
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}}
.size-chips span {{
  border: 1px solid #d8dee8;
  border-radius: 999px;
  padding: 5px 10px;
}}
.listing-main {{
  min-width: 0;
}}
.toolbar {{
  display: flex;
  gap: 10px;
  margin-bottom: 14px;
}}
.toolbar input,
.toolbar select {{
  border: 1px solid #d8dee8;
  border-radius: 10px;
  padding: 9px 10px;
}}
.toolbar input {{ flex: 1; }}
.product-grid {{
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}}
.product-card {{
  border: 1px solid #eceff3;
  border-radius: 12px;
  background: #fff;
  overflow: hidden;
}}
.product-card a {{
  display: block;
}}
.product-card img {{
  width: 100%;
  aspect-ratio: 3/4;
  object-fit: cover;
}}
.product-card h3 {{
  margin: 10px 10px 0;
  font-size: 0.95rem;
}}
.product-card p {{
  margin: 4px 10px;
  color: #525866;
  font-size: 0.86rem;
}}
.price-row {{
  display: flex;
  gap: 8px;
  align-items: center;
  margin: 6px 10px 10px;
}}
.mrp {{
  text-decoration: line-through;
  color: #8892a6;
}}
.rating {{
  margin-left: auto;
  font-weight: 700;
  color: {accent};
}}
.product-card button {{
  margin: 0 10px 12px;
  width: calc(100% - 20px);
  border: 0;
  border-radius: 10px;
  padding: 9px;
  font-weight: 700;
  cursor: pointer;
}}
@media (max-width: 980px) {{
  .listing-layout {{
    grid-template-columns: 1fr;
  }}
  .mobile-filter-toggle {{
    position: sticky;
    top: 74px;
    z-index: 22;
    display: inline-block;
    border: 1px solid #d8dee8;
    border-radius: 999px;
    background: #fff;
    padding: 8px 12px;
    margin-bottom: 10px;
    font-weight: 700;
  }}
  .mobile-filter-backdrop {{
    display: block;
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.35);
    z-index: 40;
  }}
  .filters {{
    position: fixed;
    right: -320px;
    top: 0;
    width: 300px;
    height: 100vh;
    overflow: auto;
    z-index: 41;
    border-radius: 0;
    transition: right .25s ease;
  }}
  .filters.open {{
    right: 0;
  }}
  .close-filters {{
    display: inline-block;
    border: 1px solid #d8dee8;
    border-radius: 8px;
    background: #fff;
    padding: 6px 8px;
    margin-bottom: 8px;
  }}
  .product-grid {{
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }}
}}
@media (max-width: 640px) {{
  .product-grid {{
    grid-template-columns: 1fr;
  }}
}}
"""

    @staticmethod
    def _ecommerce_product_detail_component_ts() -> str:
        return """import { Component } from '@angular/core';

@Component({
  selector: 'app-product-detail',
  templateUrl: './product-detail.component.html',
  styleUrls: ['./product-detail.component.css']
})
export class ProductDetailComponent {
  selectedImage = 'https://picsum.photos/seed/prod-detail-main/700/900';
  readonly gallery = [
    'https://picsum.photos/seed/prod-detail-main/700/900',
    'https://picsum.photos/seed/prod-detail-2/700/900',
    'https://picsum.photos/seed/prod-detail-3/700/900',
    'https://picsum.photos/seed/prod-detail-4/700/900',
  ];
  readonly sizes = ['XS', 'S', 'M', 'L', 'XL'];
  selectedSize = 'M';
}
"""

    @staticmethod
    def _ecommerce_product_detail_component_html() -> str:
        return """<section class=\"detail-layout\">
  <aside class=\"thumbs\">
    <button *ngFor=\"let img of gallery\" (click)=\"selectedImage = img\">
      <img [src]=\"img\" alt=\"thumb\" />
    </button>
  </aside>
  <div class=\"main-image\">
    <img [src]=\"selectedImage\" alt=\"product\" />
  </div>
  <article class=\"detail-panel\">
    <h2>Roadster Solid Casual Shirt</h2>
    <p class=\"rating\">4.3 ★ | 2.1k ratings</p>
    <div class=\"price\">
      <strong>$1299</strong>
      <span class=\"mrp\">$2599</span>
      <span class=\"off\">50% OFF</span>
    </div>
    <p class=\"offer\">Extra 10% off with selected cards</p>
    <h4>Select Size</h4>
    <div class=\"sizes\">
      <button *ngFor=\"let size of sizes\" [class.active]=\"size === selectedSize\" (click)=\"selectedSize = size\">{{ size }}</button>
    </div>
    <div class=\"cta\">
      <button class=\"buy\">Buy Now</button>
      <button class=\"cart\">Add to Cart</button>
    </div>
    <div class=\"meta\">
      <p>Delivery by Tomorrow</p>
      <p>Easy 14-day returns</p>
      <p>100% original products</p>
    </div>
  </article>
</section>
"""

    @staticmethod
    def _ecommerce_product_detail_component_css(theme_tokens: dict) -> str:
        primary = theme_tokens.get("primary", "#ff3f6c")
        return f""".detail-layout {{
  display: grid;
  grid-template-columns: 90px 1fr 420px;
  gap: 14px;
}}
.thumbs {{
  display: grid;
  gap: 8px;
  align-content: start;
}}
.thumbs button {{
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 0;
  overflow: hidden;
  background: #fff;
  cursor: pointer;
}}
.thumbs img {{
  width: 100%;
  aspect-ratio: 3/4;
  object-fit: cover;
}}
.main-image {{
  border: 1px solid #eceff3;
  border-radius: 12px;
  overflow: hidden;
  background: #fff;
}}
.main-image img {{
  width: 100%;
  display: block;
}}
.detail-panel {{
  border: 1px solid #eceff3;
  border-radius: 12px;
  background: #fff;
  padding: 14px;
}}
.detail-panel h2 {{
  margin: 0 0 8px;
}}
.rating {{
  color: #4b5563;
  margin: 0 0 10px;
}}
.price {{
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
}}
.price strong {{
  font-size: 1.35rem;
}}
.mrp {{
  text-decoration: line-through;
  color: #9ca3af;
}}
.off {{
  color: #16a34a;
  font-weight: 700;
}}
.offer {{
  color: #0f766e;
  font-weight: 600;
}}
.sizes {{
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}}
.sizes button {{
  border: 1px solid #d1d5db;
  border-radius: 999px;
  background: #fff;
  padding: 8px 12px;
  cursor: pointer;
}}
.sizes button.active {{
  border-color: {primary};
  color: {primary};
  font-weight: 700;
}}
.cta {{
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin: 14px 0;
}}
.cta button {{
  border: 0;
  border-radius: 10px;
  padding: 10px 12px;
  font-weight: 700;
  cursor: pointer;
}}
.buy {{
  background: {primary};
  color: #fff;
}}
.cart {{
  background: #111827;
  color: #fff;
}}
.meta p {{
  margin: 6px 0;
  color: #4b5563;
}}
@media (max-width: 1024px) {{
  .detail-layout {{
    grid-template-columns: 1fr;
  }}
  .thumbs {{
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }}
}}
"""

    @staticmethod
    def _ecommerce_catalog_module_ts() -> str:
        return """import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { ProductListComponent } from './components/product-list.component';
import { ProductDetailComponent } from './components/product-detail.component';

@NgModule({
  declarations: [ProductListComponent, ProductDetailComponent],
  imports: [CommonModule, FormsModule, RouterModule],
  exports: [ProductListComponent, ProductDetailComponent]
})
export class CatalogModule {}
"""

    @staticmethod
    def _ecommerce_home_module_ts() -> str:
        return """import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { HomeComponent } from './components/home.component';

@NgModule({
  declarations: [HomeComponent],
  imports: [CommonModule, RouterModule],
  exports: [HomeComponent]
})
export class HomeModule {}
"""

    @staticmethod
    def _ecommerce_cart_service_ts() -> str:
        return """import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

export interface CartProduct {
  id: number;
  name: string;
  brand: string;
  price: number;
  mrp: number;
  rating: number;
  img: string;
}

export interface CartItem {
  product: CartProduct;
  quantity: number;
}

@Injectable({
  providedIn: 'root'
})
export class CartService {
  private readonly storageKey = 'pf-cart-items';
  private readonly itemsSubject = new BehaviorSubject<CartItem[]>(this.loadItems());
  readonly items$ = this.itemsSubject.asObservable();

  get items(): CartItem[] {
    return this.itemsSubject.value;
  }

  add(product: CartProduct): void {
    const items = [...this.items];
    const existing = items.find(item => item.product.id === product.id);
    if (existing) {
      existing.quantity += 1;
    } else {
      items.push({ product, quantity: 1 });
    }
    this.save(items);
  }

  increase(productId: number): void {
    this.save(this.items.map(item => item.product.id === productId ? { ...item, quantity: item.quantity + 1 } : item));
  }

  decrease(productId: number): void {
    this.save(
      this.items
        .map(item => item.product.id === productId ? { ...item, quantity: item.quantity - 1 } : item)
        .filter(item => item.quantity > 0)
    );
  }

  remove(productId: number): void {
    this.save(this.items.filter(item => item.product.id !== productId));
  }

  clear(): void {
    this.save([]);
  }

  private save(items: CartItem[]): void {
    this.itemsSubject.next(items);
    try {
      localStorage.setItem(this.storageKey, JSON.stringify(items));
    } catch {
      // Keep the in-memory cart working if localStorage is blocked.
    }
  }

  private loadItems(): CartItem[] {
    try {
      const raw = localStorage.getItem(this.storageKey);
      return raw ? JSON.parse(raw) as CartItem[] : [];
    } catch {
      return [];
    }
  }
}
"""

    @staticmethod
    def _ecommerce_experience_component_ts(page: str) -> str:
        class_name = "".join(part.capitalize() for part in page.split("-")) + "Component"
        if page == "cart":
            return f"""import {{ Component }} from '@angular/core';
import {{ CartItem, CartService }} from '../../../core/services/cart.service';

@Component({{
  selector: 'app-{page}',
  templateUrl: './{page}.component.html',
  styleUrls: ['./{page}.component.css']
}})
export class {class_name} {{
  items: CartItem[] = [];

  constructor(private cartService: CartService) {{
    this.cartService.items$.subscribe(items => {{
      this.items = items;
    }});
  }}

  get subtotal(): number {{
    return this.items.reduce((total, item) => total + item.product.price * item.quantity, 0);
  }}

  get grandTotal(): number {{
    return this.subtotal > 0 ? this.subtotal + 49 : 0;
  }}

  increase(productId: number): void {{
    this.cartService.increase(productId);
  }}

  decrease(productId: number): void {{
    this.cartService.decrease(productId);
  }}

  remove(productId: number): void {{
    this.cartService.remove(productId);
  }}
}}
"""
        return f"""import {{ Component }} from '@angular/core';

@Component({{
  selector: 'app-{page}',
  templateUrl: './{page}.component.html',
  styleUrls: ['./{page}.component.css']
}})
export class {class_name} {{
  readonly title = '{page.replace("-", " ").title()}';
  readonly highlights = ['Premium UX', 'Color-rich design', 'Connected flow'];
}}
"""

    @staticmethod
    def _ecommerce_experience_component_html(page: str) -> str:
        if page == "cart":
            return """<section class="experience-shell">
  <div class="experience-hero">
    <p>SHOPPING BAG</p>
    <h1>Your selected styles</h1>
    <span>{{ items.length }} item groups ready for checkout</span>
  </div>

  <div class="cart-grid" *ngIf="items.length; else emptyCart">
    <div>
      <article class="cart-item" *ngFor="let item of items">
        <img [src]="item.product.img" [alt]="item.product.name" />
        <div>
          <h3>{{ item.product.brand }}</h3>
          <p>{{ item.product.name }}</p>
          <strong>${{ item.product.price }}</strong>
        </div>
        <div class="quantity">
          <button (click)="decrease(item.product.id)">-</button>
          <span>{{ item.quantity }}</span>
          <button (click)="increase(item.product.id)">+</button>
        </div>
        <button class="ghost" (click)="remove(item.product.id)">Remove</button>
      </article>
    </div>

    <aside class="summary-card">
      <h2>Price Details</h2>
      <p><span>Subtotal</span><strong>${{ subtotal }}</strong></p>
      <p><span>Shipping</span><strong>$49</strong></p>
      <p class="total"><span>Total</span><strong>${{ grandTotal }}</strong></p>
      <a class="primary-action" [routerLink]="['/checkout']">Proceed to Checkout</a>
    </aside>
  </div>

  <ng-template #emptyCart>
    <div class="empty-state">
      <h2>Your cart is waiting for color.</h2>
      <p>Add products from the catalog to see totals and checkout actions here.</p>
      <a class="primary-action" [routerLink]="['/products']">Shop Products</a>
    </div>
  </ng-template>
</section>
"""
        page_copy = {
            "login": ("Welcome back", "Sign in to sync wishlist, cart, orders, and premium member offers.", "Login"),
            "signup": ("Create your style account", "Join the studio for faster checkout, saved looks, and order tracking.", "Create Account"),
            "checkout": ("Checkout", "Confirm delivery, payment mode, and place your order.", "Place Order"),
            "wishlist": ("Wishlist", "Save bold looks and move favorites into your cart anytime.", "Move Favorites"),
            "account": ("Account", "Manage profile, addresses, orders, and style preferences.", "Update Profile"),
            "admin": ("Admin Studio", "Track orders, revenue, inventory, and product launches.", "Save Dashboard"),
        }
        title, subtitle, action = page_copy.get(page, ("Experience", "Premium generated page.", "Continue"))
        return f"""<section class="experience-shell">
  <div class="experience-hero">
    <p>{page.upper()}</p>
    <h1>{title}</h1>
    <span>{subtitle}</span>
  </div>

  <div class="experience-card">
    <div class="form-grid">
      <label>
        <span>Email</span>
        <input placeholder="you@example.com" />
      </label>
      <label>
        <span>Name / Reference</span>
        <input placeholder="Enter details" />
      </label>
      <label class="wide">
        <span>Notes</span>
        <textarea placeholder="Add delivery, account, or admin details"></textarea>
      </label>
    </div>
    <div class="highlight-row">
      <span *ngFor="let item of highlights">{{{{ item }}}}</span>
    </div>
    <button class="primary-action">{action}</button>
  </div>
</section>
"""

    @staticmethod
    def _ecommerce_experience_component_css(_page: str) -> str:
        return """:host {
  display: block;
}
.experience-shell {
  display: grid;
  gap: 18px;
}
.experience-hero,
.experience-card,
.summary-card,
.empty-state,
.cart-item {
  border: 1px solid rgba(255,255,255,.68);
  background: rgba(255,255,255,.78);
  border-radius: 24px;
  box-shadow: 0 24px 60px rgba(15,23,42,.10);
  backdrop-filter: blur(18px);
}
.experience-hero {
  min-height: 220px;
  padding: 34px;
  color: #fff;
  display: grid;
  align-content: end;
  background:
    linear-gradient(135deg, rgba(17,24,39,.88), rgba(124,58,237,.66), rgba(255,63,108,.64)),
    url('https://picsum.photos/seed/experience-hero/1400/600') center/cover;
}
.experience-hero p,
.experience-hero h1,
.experience-hero span {
  margin: 0;
}
.experience-hero h1 {
  font-size: clamp(2rem, 6vw, 4.5rem);
  line-height: .95;
}
.experience-card,
.empty-state,
.summary-card {
  padding: 24px;
}
.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}
label {
  display: grid;
  gap: 8px;
  font-weight: 800;
}
.wide {
  grid-column: 1 / -1;
}
input,
textarea {
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 13px 14px;
  font: inherit;
  background: rgba(255,255,255,.92);
}
textarea {
  min-height: 110px;
}
.highlight-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin: 18px 0;
}
.highlight-row span {
  border-radius: 999px;
  padding: 8px 12px;
  color: #7c2d12;
  background: linear-gradient(135deg, #ffedd5, #fce7f3);
  font-weight: 900;
}
.primary-action {
  display: inline-flex;
  justify-content: center;
  align-items: center;
  border: 0;
  border-radius: 999px;
  padding: 13px 20px;
  color: #fff;
  font-weight: 900;
  text-decoration: none;
  background: linear-gradient(135deg, #ff3f6c, #7c3aed, #06b6d4);
  box-shadow: 0 18px 38px rgba(124,58,237,.22);
}
.cart-grid {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 16px;
}
.cart-item {
  display: grid;
  grid-template-columns: 92px 1fr auto auto;
  gap: 14px;
  align-items: center;
  padding: 14px;
  margin-bottom: 12px;
}
.cart-item img {
  width: 92px;
  height: 120px;
  object-fit: cover;
  border-radius: 16px;
}
.cart-item h3,
.cart-item p {
  margin: 0 0 5px;
}
.quantity {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: 1px solid #e2e8f0;
  border-radius: 999px;
  padding: 6px;
}
.quantity button,
.ghost {
  border: 0;
  border-radius: 999px;
  padding: 8px 11px;
  font-weight: 900;
  cursor: pointer;
}
.quantity button {
  color: #fff;
  background: #111827;
}
.ghost {
  background: #fff1f2;
  color: #be123c;
}
.summary-card {
  height: fit-content;
}
.summary-card p {
  display: flex;
  justify-content: space-between;
}
.summary-card .total {
  border-top: 1px solid #e2e8f0;
  padding-top: 12px;
  font-size: 1.2rem;
}
@media (max-width: 900px) {
  .cart-grid,
  .form-grid {
    grid-template-columns: 1fr;
  }
  .cart-item {
    grid-template-columns: 80px 1fr;
  }
}
"""

    @staticmethod
    def _ecommerce_global_css(theme_tokens: dict) -> str:
        primary = theme_tokens.get("primary", "#ff3f6c")
        accent = theme_tokens.get("accent", "#7c3aed")
        return f"""/* Premium ecommerce visual floor: keeps generated sites colorful even if LLM polish is conservative. */
:root {{
  --pf-commerce-primary: {primary};
  --pf-commerce-accent: {accent};
  --pf-commerce-cyan: #06b6d4;
  --pf-commerce-ink: #111827;
  --pf-commerce-card: rgba(255,255,255,.82);
}}
body {{
  background:
    radial-gradient(circle at top left, color-mix(in srgb, var(--pf-commerce-primary) 22%, transparent), transparent 28rem),
    radial-gradient(circle at top right, color-mix(in srgb, var(--pf-commerce-cyan) 22%, transparent), transparent 28rem),
    linear-gradient(135deg, #fff7fb 0%, #eef5ff 48%, #fffaf0 100%);
}}
button,
a {{
  transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
}}
button:hover,
a:hover {{
  transform: translateY(-1px);
}}
img {{
  max-width: 100%;
}}
"""

    @staticmethod
    def _ecommerce_app_routing_ts() -> str:
        return """import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { HomeComponent } from './features/home/components/home.component';
import { ProductListComponent } from './features/catalog/components/product-list.component';
import { ProductDetailComponent } from './features/catalog/components/product-detail.component';
import { CartComponent } from './features/experience/components/cart.component';
import { LoginComponent } from './features/experience/components/login.component';
import { SignupComponent } from './features/experience/components/signup.component';
import { CheckoutComponent } from './features/experience/components/checkout.component';
import { WishlistComponent } from './features/experience/components/wishlist.component';
import { AccountComponent } from './features/experience/components/account.component';
import { AdminComponent } from './features/experience/components/admin.component';

const routes: Routes = [
  { path: '', component: HomeComponent },
  { path: 'products', component: ProductListComponent },
  { path: 'product/:id', component: ProductDetailComponent },
  { path: 'cart', component: CartComponent },
  { path: 'auth/login', component: LoginComponent },
  { path: 'auth/signup', component: SignupComponent },
  { path: 'checkout', component: CheckoutComponent },
  { path: 'wishlist', component: WishlistComponent },
  { path: 'account', component: AccountComponent },
  { path: 'admin', component: AdminComponent },
  { path: '**', redirectTo: '' }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule {}
"""

    @staticmethod
    def _ecommerce_app_module_ts() -> str:
        return """import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { HttpClientModule } from '@angular/common/http';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { HomeModule } from './features/home/home.module';
import { CatalogModule } from './features/catalog/catalog.module';
import { CartComponent } from './features/experience/components/cart.component';
import { LoginComponent } from './features/experience/components/login.component';
import { SignupComponent } from './features/experience/components/signup.component';
import { CheckoutComponent } from './features/experience/components/checkout.component';
import { WishlistComponent } from './features/experience/components/wishlist.component';
import { AccountComponent } from './features/experience/components/account.component';
import { AdminComponent } from './features/experience/components/admin.component';

@NgModule({
  declarations: [
    AppComponent,
    CartComponent,
    LoginComponent,
    SignupComponent,
    CheckoutComponent,
    WishlistComponent,
    AccountComponent,
    AdminComponent
  ],
  imports: [
    BrowserModule,
    HttpClientModule,
    FormsModule,
    ReactiveFormsModule,
    BrowserAnimationsModule,
    AppRoutingModule,
    HomeModule,
    CatalogModule
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule {}
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

  location /api/ {
    proxy_pass http://backend:8080/api/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  }

  location / {
    try_files $uri $uri/ /index.html;
  }
}
"""
