from pydantic import BaseModel, Field


class WebDiscoveryPreviewRequest(BaseModel):
    prompt: str = Field(min_length=5)
    domain_hint: str | None = None
    website_like: str | None = None


class WebDiscoveryPreviewResponse(BaseModel):
    query: str
    trusted_results: list[dict]
    extracted_features: list[str]
    extracted_entities: list[str]
    extracted_routes: list[str]
    extracted_components: list[str]
    backend_patterns: list[str]
    suggested_architecture: list[str]
    draft_enriched_prompt: str
