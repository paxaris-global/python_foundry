from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class TrustedWebResult(BaseModel):
    """A single web-discovery result that passed trust filtering."""

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "example": {
                "url": "https://example.com/architecture",
                "title": "Shopify Architecture Overview",
                "snippet": "Shopify uses a modular monolith with event-driven …",
                "source_type": "web",
            }
        },
    )

    url: str = Field(description="URL of the discovered web page.")
    title: Optional[str] = Field(default=None, description="Page title or heading.")
    snippet: Optional[str] = Field(default=None, description="Short excerpt from the page content.")
    source_type: Optional[str] = Field(default=None, description="Origin classification (e.g. 'web', 'docs').")


class WebDiscoveryPreviewRequest(BaseModel):
    """Request a preview of what web-discovery would find for a given prompt."""

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "prompt": "Build an e-commerce platform like Shopify",
            "domain_hint": "ecommerce",
            "website_like": "https://www.shopify.com",
        }
    })

    prompt: str = Field(min_length=5, description="Natural-language description of the desired application.")
    domain_hint: Optional[str] = Field(default=None, description="Optional domain classification hint to guide discovery.")
    website_like: Optional[str] = Field(default=None, description="Reference website URL to inspire discovery.")


class WebDiscoveryPreviewResponse(BaseModel):
    """Aggregated web-discovery results including extracted patterns and an enriched prompt draft."""

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "query": "Shopify ecommerce architecture patterns",
            "trusted_results": [{"url": "https://example.com", "title": "Shopify Architecture"}],
            "extracted_features": ["product-catalog", "cart", "checkout"],
            "extracted_entities": ["Product", "Order", "Customer"],
            "extracted_routes": ["/products", "/cart", "/checkout"],
            "extracted_components": ["ProductList", "CartSummary"],
            "backend_patterns": ["microservices", "event-driven"],
            "suggested_architecture": ["API gateway", "message queue"],
            "draft_enriched_prompt": "Generate an e-commerce platform …",
        }
    })

    query: str = Field(description="Search query that was executed.")
    trusted_results: list[TrustedWebResult] = Field(description="Filtered web results from trusted sources.")
    extracted_features: list[str] = Field(description="Application features discovered from web sources.")
    extracted_entities: list[str] = Field(description="Domain entities identified (e.g. 'Product', 'Order').")
    extracted_routes: list[str] = Field(description="API or page routes extracted from reference sites.")
    extracted_components: list[str] = Field(description="UI components identified from reference sites.")
    backend_patterns: list[str] = Field(description="Backend architectural patterns found.")
    suggested_architecture: list[str] = Field(description="High-level architecture recommendations.")
    draft_enriched_prompt: str = Field(description="Enriched prompt draft incorporating discovery results.")
