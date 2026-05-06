from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import ExecutionModeValue


class TrustedSource(BaseModel):
    """A web source that passed trust filtering during prompt assembly."""

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "example": {
                "url": "https://example.com/crm-patterns",
                "title": "CRM Architecture Patterns",
            }
        },
    )

    url: str = Field(description="URL of the trusted source.")
    title: Optional[str] = Field(default=None, description="Page title or heading of the source.")


class FinalPromptResponse(BaseModel):
    """Debug view of the fully-assembled prompt artifact for a generation job."""

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "job_id": "b1e4a2f0-1234-5678-abcd-ef0123456789",
            "project_id": "c2f5b3e1-5678-1234-abcd-ef0123456789",
            "raw_user_prompt": "Generate a CRM application with contact management",
            "parsed_prompt": {"summary": "CRM app", "tokens": ["CRM", "contact"], "entities": ["Contact"], "feature_hints": ["contacts-crud"]},
            "parsed_prompt_summary": {"summary": "CRM app", "token_count": 2, "entities": ["Contact"], "feature_hints": ["contacts-crud"]},
            "expanded_features": ["authentication", "dashboard", "contacts-crud"],
            "execution_mode": "generate",
            "rag_summary": {"hits": 3},
            "rag_context_summary": {"top_snippet": "Spring Security config…"},
            "web_discovery_summary": {"sources_found": 2},
            "adaptation_context_summary": {},
            "trusted_sources": [{"url": "https://example.com", "title": "CRM Patterns"}],
            "pre_final_prompt": "Generate a production-ready CRM…",
            "final_enriched_prompt": "Generate a production-ready CRM application…",
            "artifact_text_path": "/data/artifacts/prompt.txt",
            "artifact_json_path": "/data/artifacts/prompt.json",
            "created_at": "2025-06-01T12:00:00",
        }
    })

    job_id: str = Field(description="UUID of the parent job.")
    project_id: Optional[str] = Field(description="UUID of the associated project, if generation completed.")
    raw_user_prompt: str = Field(description="Original user-supplied prompt text.")
    parsed_prompt: dict[str, Any] = Field(description="Structured representation produced by the prompt parser.")
    parsed_prompt_summary: dict[str, Any] = Field(description="Compact summary of the parsed prompt (token count, entities, etc.).")
    expanded_features: list[str] = Field(description="Final feature list after expansion and sanitisation.")
    execution_mode: ExecutionModeValue = Field(description="Execution mode used for this job.")
    rag_summary: dict[str, Any] = Field(description="Summary of RAG retrieval results used.")
    rag_context_summary: dict[str, Any] = Field(description="Condensed RAG context fed into the prompt.")
    web_discovery_summary: dict[str, Any] = Field(description="Summary of web-discovery results used.")
    adaptation_context_summary: dict[str, Any] = Field(description="Context used when adapting an existing project.")
    trusted_sources: list[TrustedSource] = Field(description="Web sources that passed trust filtering.")
    pre_final_prompt: Optional[str] = Field(description="Prompt text before the final enrichment pass.")
    final_enriched_prompt: str = Field(description="The complete prompt sent to the LLM.")
    artifact_text_path: Optional[str] = Field(description="Path to the persisted plain-text artifact.")
    artifact_json_path: Optional[str] = Field(description="Path to the persisted JSON artifact.")
    created_at: str = Field(description="ISO-8601 timestamp of artifact creation.")
