import json
import re
from pathlib import Path


class SyntaxChecker:
    def check(self, project_root: Path) -> dict:
        failed = []
        html_invalid = []
        java_string_issues = []
        route_guard_issues = []

        for path in project_root.rglob("*.json"):
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                failed.append(str(path.relative_to(project_root)).replace("\\", "/"))

        for path in project_root.rglob("*.html"):
            content = path.read_text(encoding="utf-8", errors="ignore")
            if self._has_unbalanced_html(content):
                html_invalid.append(str(path.relative_to(project_root)).replace("\\", "/"))

        for path in project_root.rglob("*.java"):
            content = path.read_text(encoding="utf-8", errors="ignore")
            if self._has_unclosed_java_string(content):
                java_string_issues.append(str(path.relative_to(project_root)).replace("\\", "/"))

        routing = project_root / "frontend/src/app/app-routing.module.ts"
        app_module = project_root / "frontend/src/app/app.module.ts"
        if routing.exists() and app_module.exists():
            route_guard_issues.extend(self._route_module_guard(routing, app_module))

        ok = not (failed or html_invalid or java_string_issues or route_guard_issues)
        return {
            "json_invalid": failed,
            "html_invalid": html_invalid,
            "java_string_issues": java_string_issues,
            "route_module_issues": route_guard_issues,
            "ok": ok,
        }

    @staticmethod
    def _has_unclosed_java_string(content: str) -> bool:
        escaped = False
        in_string = False
        for ch in content:
            if escaped:
                escaped = False
                continue
            if ch == "\\":
                escaped = True
                continue
            if ch == '"':
                in_string = not in_string
        return in_string

    @staticmethod
    def _has_unbalanced_html(content: str) -> bool:
        pattern = re.compile(r"<(/?)([a-zA-Z][a-zA-Z0-9-]*)[^>]*>")
        stack: list[str] = []
        voids = {"br", "hr", "img", "input", "meta", "link", "source"}
        for match in pattern.finditer(content):
            is_close = match.group(1) == "/"
            tag = match.group(2).lower()
            token = match.group(0).strip()
            if tag in voids or token.endswith("/>"):
                continue
            if not is_close:
                stack.append(tag)
            else:
                if not stack or stack[-1] != tag:
                    return True
                stack.pop()
        return bool(stack)

    @staticmethod
    def _route_module_guard(routing_file: Path, app_module_file: Path) -> list[str]:
        issues: list[str] = []
        routing_src = routing_file.read_text(encoding="utf-8", errors="ignore")
        module_src = app_module_file.read_text(encoding="utf-8", errors="ignore")
        route_components = set(re.findall(r"component:\s*([A-Za-z0-9_]+)", routing_src))
        declared_components = set(re.findall(r"declarations:\s*\[([^\]]*)\]", module_src, re.S))
        imported_symbols = set(re.findall(r"import\s*\{\s*([^}]+)\s*\}", module_src))
        flat_declared = set()
        for block in declared_components:
            for item in block.split(","):
                token = item.strip()
                if token:
                    flat_declared.add(token)
        flat_imports = set()
        for block in imported_symbols:
            for item in block.split(","):
                token = item.strip()
                if token:
                    flat_imports.add(token)
        for comp in sorted(route_components):
            if comp not in flat_declared and comp not in flat_imports:
                issues.append(f"route_component_missing:{comp}")
        return issues
