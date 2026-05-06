from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = Field(default="development", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    secret_key: str = Field(default="change_me", alias="SECRET_KEY")

    postgres_user: str = Field(default="ai_codegen", alias="POSTGRES_USER")
    postgres_password: str = Field(default="ai_codegen_pass", alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(default="ai_codegen_db", alias="POSTGRES_DB")
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")

    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    celery_broker_url: str = Field(default="redis://localhost:6379/0", alias="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/1", alias="CELERY_RESULT_BACKEND")

    chroma_persist_directory: str = Field(default="./chroma_data", alias="CHROMA_PERSIST_DIRECTORY")
    llm_provider: str = Field(default="anthropic", alias="LLM_PROVIDER")
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(default="claude-3-5-sonnet-latest", alias="ANTHROPIC_MODEL")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    embedding_model: str = Field(default="text-embedding-3-small", alias="EMBEDDING_MODEL")
    log_llm_prompts: bool = Field(default=False, alias="LOG_LLM_PROMPTS")
    llm_prompt_log_max_chars: int = Field(default=20000, alias="LLM_PROMPT_LOG_MAX_CHARS")

    search_provider: str = Field(default="serpapi", alias="SEARCH_PROVIDER")
    search_api_key: str | None = Field(default=None, alias="SEARCH_API_KEY")
    search_engine: str = Field(default="google_light", alias="SEARCH_ENGINE")
    fallback_search_provider: str = Field(default="duckduckgo", alias="FALLBACK_SEARCH_PROVIDER")
    github_token: str | None = Field(default=None, alias="GITHUB_TOKEN")
    search_timeout_seconds: int = Field(default=10, alias="SEARCH_TIMEOUT_SECONDS")
    enable_playwright: bool = Field(default=False, alias="ENABLE_PLAYWRIGHT")
    allowed_web_domains: str = Field(default="github.com,docs.github.com,spring.io,angular.dev", alias="ALLOWED_WEB_DOMAINS")
    denied_web_domains: str = Field(default="", alias="DENIED_WEB_DOMAINS")
    max_web_results: int = Field(default=10, alias="MAX_WEB_RESULTS")
    max_web_fetch_pages: int = Field(default=5, alias="MAX_WEB_FETCH_PAGES")
    max_repo_files: int = Field(default=150, alias="MAX_REPO_FILES")
    max_prompt_debug_size: int = Field(default=200000, alias="MAX_PROMPT_DEBUG_SIZE")

    max_rag_results: int = Field(default=8, alias="MAX_RAG_RESULTS")
    max_generation_file_size: int = Field(default=500000, alias="MAX_GENERATION_FILE_SIZE")
    max_generated_file_count: int = Field(default=600, alias="MAX_GENERATED_FILE_COUNT")
    max_zip_size_mb: int = Field(default=50, alias="MAX_ZIP_SIZE_MB")
    rag_min_similarity: float = Field(default=0.0, alias="RAG_MIN_SIMILARITY")
    
    # LLM settings
    anthropic_timeout_seconds: int = Field(default=60, alias="ANTHROPIC_TIMEOUT_SECONDS")
    openai_timeout_seconds: int = Field(default=60, alias="OPENAI_TIMEOUT_SECONDS")

    downloads_dir_path: str | None = Field(default=None, alias="DOWNLOADS_DIR")

    @property
    def sqlalchemy_database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def base_dir(self) -> Path:
        return Path(__file__).resolve().parents[2]

    @property
    def generated_projects_dir(self) -> Path:
        return self.base_dir / "generated_projects"

    @property
    def downloads_dir(self) -> Path:
        if self.downloads_dir_path:
            return Path(self.downloads_dir_path).expanduser().resolve()
        return Path.home() / "Downloads"

    @property
    def allowed_domains_set(self) -> set[str]:
        return {item.strip().lower() for item in self.allowed_web_domains.split(",") if item.strip()}

    @property
    def denied_domains_set(self) -> set[str]:
        return {item.strip().lower() for item in self.denied_web_domains.split(",") if item.strip()}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
