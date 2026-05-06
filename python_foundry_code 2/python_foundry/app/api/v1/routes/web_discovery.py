from fastapi import APIRouter

from app.api.deps import DBSession
from app.schemas.web_discovery import WebDiscoveryPreviewRequest, WebDiscoveryPreviewResponse
from app.services.generation.prompt_parser import PromptParser
from app.services.intelligence.domain_classifier import DomainClassifier
from app.services.intelligence.prompt_enricher import PromptEnricher
from app.services.web_discovery.web_discovery_orchestrator import WebDiscoveryOrchestrator

router = APIRouter(prefix="/web-discovery", tags=["web-discovery"])


@router.post("/preview")
def web_discovery_preview(payload: WebDiscoveryPreviewRequest, db: DBSession) -> WebDiscoveryPreviewResponse:
    parsed = PromptParser().parse_prompt(payload.prompt)
    domain = payload.domain_hint or DomainClassifier().classify(parsed)

    query_basis = payload.website_like or payload.prompt
    query = f"{query_basis} {domain} architecture patterns"

    discovery = WebDiscoveryOrchestrator(db).discover(query=query, job_id=None, module_type=domain, tags=[])

    draft_enriched_prompt = PromptEnricher().enrich(
        original_prompt=payload.prompt,
        project_spec={
            "description": payload.prompt,
            "project_name": parsed.get("project_name", "web-inspired-project"),
            "features": discovery.get("extracted_features", []),
            "domain": domain,
        },
        api_contract={"paths": {}},
        rag_context=[],
        fallback_context={"strategy": "web_discovery_preview"},
    )

    return WebDiscoveryPreviewResponse(
        query=query,
        trusted_results=discovery.get("trusted_results", []),
        extracted_features=discovery.get("extracted_features", []),
        extracted_entities=discovery.get("extracted_entities", []),
        extracted_routes=discovery.get("extracted_routes", []),
        extracted_components=discovery.get("extracted_components", []),
        backend_patterns=discovery.get("backend_patterns", []),
        suggested_architecture=discovery.get("suggested_architecture", []),
        draft_enriched_prompt=draft_enriched_prompt,
    )
