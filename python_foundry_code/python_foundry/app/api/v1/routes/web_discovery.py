from fastapi import APIRouter

from app.api.deps import DBSession
from app.core.exceptions import ServiceUnavailableException
from app.core.logging import get_logger
from app.schemas.common import ErrorResponse
from app.schemas.web_discovery import WebDiscoveryPreviewRequest, WebDiscoveryPreviewResponse
from app.services.generation.prompt_parser import PromptParser
from app.services.intelligence.domain_classifier import DomainClassifier
from app.services.intelligence.prompt_enricher import PromptEnricher
from app.services.web_discovery.web_discovery_orchestrator import WebDiscoveryOrchestrator

router = APIRouter(prefix="/web-discovery", tags=["Web Discovery"])
logger = get_logger(__name__)


@router.post(
    "/preview",
    response_model=WebDiscoveryPreviewResponse,
    summary="Preview web discovery results",
    description="Runs web discovery for a prompt without starting a generation job. "
                "Returns extracted features, entities, routes, backend patterns, and a draft enriched prompt.",
    responses={
        422: {"description": "Invalid preview request.", "model": ErrorResponse},
        503: {"description": "Web discovery service unavailable.", "model": ErrorResponse},
    },
)
def web_discovery_preview(payload: WebDiscoveryPreviewRequest, db: DBSession) -> WebDiscoveryPreviewResponse:
    parsed = PromptParser().parse_prompt(payload.prompt)
    domain = payload.domain_hint or DomainClassifier().classify(parsed)

    query_basis = payload.website_like or payload.prompt
    query = f"{query_basis} {domain} architecture patterns"

    try:
        discovery = WebDiscoveryOrchestrator(db).discover(query=query, job_id=None, module_type=domain, tags=[])
    except Exception:
        logger.exception("Web discovery preview failed for query=%s", query[:100])
        raise ServiceUnavailableException("Web discovery failed. External search services may be unavailable.")

    try:
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
    except Exception:
        logger.exception("Prompt enrichment failed during web discovery preview")
        raise ServiceUnavailableException("Failed to enrich prompt with web discovery results.")

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
