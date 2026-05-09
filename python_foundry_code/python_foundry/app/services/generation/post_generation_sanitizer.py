import re
from pathlib import Path


SMART_QUOTES_MAP = {
    "\u2018": "'",
    "\u2019": "'",
    "\u201c": '"',
    "\u201d": '"',
}


class PostGenerationSanitizer:
    @staticmethod
    def sanitize_text(content: str) -> str:
        sanitized = content
        for src, target in SMART_QUOTES_MAP.items():
            sanitized = sanitized.replace(src, target)
        return sanitized

    def sanitize_file_content(self, relative_path: str, content: str) -> str:
        sanitized = self.sanitize_text(content)
        if relative_path.endswith(".java"):
            # Normalize common curly quote side effects in Java source.
            sanitized = sanitized.replace("”", '"').replace("“", '"')
        if relative_path.endswith(".html"):
            sanitized = self._auto_fix_common_html_imbalance(sanitized)
        return sanitized

    @staticmethod
    def _auto_fix_common_html_imbalance(content: str) -> str:
        stripped = content.rstrip()
        if not stripped.endswith("</div>"):
            return content
        section_open = len(re.findall(r"<section\b", content))
        section_close = len(re.findall(r"</section>", content))
        div_open = len(re.findall(r"<div\b", content))
        div_close = len(re.findall(r"</div>", content))
        # Common generator slip: outer <section> closed as </div>.
        if section_open == section_close + 1 and div_open == div_close:
            return stripped[:-6] + "</section>\n"
        return content

    @staticmethod
    def has_unclosed_java_string(content: str) -> bool:
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
    def has_unbalanced_html_tags(content: str) -> bool:
        # Fast heuristic for generated Angular templates.
        tag_pattern = re.compile(r"<(/?)([a-zA-Z][a-zA-Z0-9-]*)[^>]*>")
        stack: list[str] = []
        void_tags = {"br", "hr", "img", "input", "meta", "link", "source"}
        for match in tag_pattern.finditer(content):
            closing = match.group(1) == "/"
            tag = match.group(2).lower()
            full = match.group(0).strip()
            if tag in void_tags or full.endswith("/>"):
                continue
            if not closing:
                stack.append(tag)
            else:
                if not stack or stack[-1] != tag:
                    return True
                stack.pop()
        return bool(stack)

    def sanitize_generated_tree(self, project_root: Path) -> dict:
        issues: list[str] = []
        touched = 0
        for file_path in project_root.rglob("*"):
            if not file_path.is_file():
                continue
            if file_path.suffix.lower() not in {".java", ".html", ".ts", ".css", ".md", ".yml", ".yaml", ".json"}:
                continue
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            sanitized = self.sanitize_text(content)
            if sanitized != content:
                file_path.write_text(sanitized, encoding="utf-8")
                touched += 1
            if file_path.suffix.lower() == ".java" and self.has_unclosed_java_string(sanitized):
                issues.append(f"unclosed_java_string:{file_path}")
            if file_path.suffix.lower() == ".html" and self.has_unbalanced_html_tags(sanitized):
                issues.append(f"unbalanced_html:{file_path}")
        return {"touched_files": touched, "issues": issues}

