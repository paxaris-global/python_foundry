API_PREFIX = "/api/v1"

SUPPORTED_BACKENDS = {"springboot"}
SUPPORTED_FRONTENDS = {"angular"}

# Bump this when template boilerplate changes.
# It is included in the generation fingerprint to avoid serving stale cached UI.
CODEGEN_TEMPLATE_VERSION = "2026-04-30-storefront-v1"

ALLOWED_GENERATED_EXTENSIONS = {
    ".java",
    ".xml",
    ".yml",
    ".yaml",
    ".properties",
    ".json",
    ".md",
    ".ts",
    ".html",
    ".css",
    ".scss",
    ".js",
    ".env",
    ".conf",
    ".txt",
    ".sql",
    ".gitignore",
    ".dockerignore",
}

REQUIRED_SKELETON_DIRS = [
    "backend",
    "backend/src/main/resources",
    "frontend",
    "frontend/src",
    "frontend/src/app",
    "_meta",
    ".github/workflows",
]

MANDATORY_OUTPUT_FILES = [
    "backend/pom.xml",
    "backend/Dockerfile",
    "frontend/package.json",
    "frontend/Dockerfile",
    "frontend/nginx.conf",
    "docker-compose.yml",
    "README.md",
    ".env.example",
    "_meta/final_enriched_prompt.txt",
    "_meta/final_enriched_prompt.json",
]

CRITICAL_NON_EMPTY_FILES = [
    "backend/pom.xml",
    "backend/src/main/resources/application.yml",
    "frontend/package.json",
    "frontend/src/main.ts",
    "README.md",
]

DEFAULT_DOMAIN = "general"
RAG_SCORE_THRESHOLD = 0.45
