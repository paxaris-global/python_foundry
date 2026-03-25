from pydantic import BaseModel


class FinalPromptResponse(BaseModel):
    job_id: str
    project_id: str | None
    raw_user_prompt: str
    parsed_prompt: dict
    parsed_prompt_summary: dict
    expanded_features: list[str]
    execution_mode: str
    rag_summary: dict
    rag_context_summary: dict
    web_discovery_summary: dict
    adaptation_context_summary: dict
    trusted_sources: list[dict]
    pre_final_prompt: str | None
    final_enriched_prompt: str
    artifact_text_path: str | None
    artifact_json_path: str | None
    created_at: str
