from typing import Optional

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.web_discovery_run import WebDiscoveryRun
from app.models.web_source import WebSource
from app.services.rag.source_ingestor import RAGSourceIngestor
from app.services.web_discovery.backend_pattern_extractor import BackendPatternExtractor
from app.services.web_discovery.component_extractor import ComponentExtractor
from app.services.web_discovery.entity_extractor import EntityExtractor
from app.services.web_discovery.feature_extractor import FeatureExtractor
from app.services.web_discovery.html_extractor import HtmlExtractor
from app.services.web_discovery.page_fetcher import PageFetcher
from app.services.web_discovery.repo_analyzer import RepoAnalyzer
from app.services.web_discovery.repo_fetcher import RepoFetcher
from app.services.web_discovery.result_ranker import ResultRanker
from app.services.web_discovery.route_extractor import RouteExtractor
from app.services.web_discovery.search_client import SearchClient
from app.services.web_discovery.trusted_source_filter import TrustedSourceFilter
from app.services.web_discovery.ui_pattern_extractor import UIPatternExtractor
from app.services.web_discovery.web_knowledge_builder import WebKnowledgeBuilder


class WebDiscoveryOrchestrator:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.search_client = SearchClient()
        self.trusted_filter = TrustedSourceFilter()
        self.ranker = ResultRanker()
        self.page_fetcher = PageFetcher()
        self.repo_fetcher = RepoFetcher()
        self.html_extractor = HtmlExtractor()
        self.repo_analyzer = RepoAnalyzer()
        self.ui_extractor = UIPatternExtractor()
        self.feature_extractor = FeatureExtractor()
        self.entity_extractor = EntityExtractor()
        self.route_extractor = RouteExtractor()
        self.component_extractor = ComponentExtractor()
        self.backend_extractor = BackendPatternExtractor()
        self.builder = WebKnowledgeBuilder()
        self.ingestor = RAGSourceIngestor(db)

    def search_web_sources(self, discovery_queries: list[str]) -> list[dict]:
        if not discovery_queries:
            return []

        results: list[dict] = []
        for query in discovery_queries:
            for item in self.search_client.search(query):
                results.append({**item, "search_query": query})
        return self.search_client._dedupe_results(results, self.settings.max_web_results)

    def filter_trusted_sources(self, raw_results: list[dict]) -> list[dict]:
        if not raw_results:
            return []
        return self.trusted_filter.filter(raw_results)

    def rank_trusted_sources(self, discovery_queries: list[str], trusted_results: list[dict]) -> list[dict]:
        if not trusted_results:
            return []
        ranking_query = " ".join(discovery_queries[:2]) if discovery_queries else ""
        return self.ranker.rank(ranking_query, trusted_results)

    def fetch_shortlisted_sources(self, ranked_results: list[dict], discovery_decision: dict) -> list[dict]:
        if not discovery_decision.get("should_run") or not ranked_results:
            return []

        fetched_payloads: list[dict] = []
        for result in ranked_results[: self.settings.max_web_fetch_pages]:
            url = result.get("url", "")
            source_payload = {
                "source": result,
                "page_data": {"url": url, "text": "", "headings": [], "nav_links": [], "title": result.get("title", "")},
                "repo_analysis": {},
            }

            if "github.com" in url:
                repo_payload = self.repo_fetcher.fetch_github_repo(url)
                source_payload["repo_analysis"] = self.repo_analyzer.analyze(repo_payload)
                source_payload["page_data"]["text"] = repo_payload.get("readme", "")
            else:
                page_resp = self.page_fetcher.fetch(url)
                if page_resp.get("status") == "ok":
                    source_payload["page_data"] = self.html_extractor.extract(page_resp.get("html", ""), url)

            fetched_payloads.append(source_payload)

        return fetched_payloads

    def extract_structured_knowledge(self, ranked_results: list[dict], fetched_payloads: list[dict]) -> dict:
        if not ranked_results:
            return self.builder.build([], [])

        extracted_items: list[dict] = []
        for payload in fetched_payloads:
            result = payload.get("source", {})
            page_data = payload.get("page_data", {})
            repo_analysis = payload.get("repo_analysis", {})

            extracted_items.append(
                {
                    "url": result.get("url"),
                    "title": page_data.get("title") or result.get("title"),
                    "trust_score": result.get("trust_score", 0.0),
                    "features": self.feature_extractor.extract(page_data),
                    "entities": self.entity_extractor.extract(page_data),
                    "routes": self.route_extractor.extract(page_data),
                    "components": self.component_extractor.extract(page_data),
                    "backend_patterns": self.backend_extractor.extract(page_data, repo_analysis),
                    "ui_patterns": self.ui_extractor.extract(page_data),
                    "text": page_data.get("text", "")[:12000],
                }
            )

        return self.builder.build(ranked_results, extracted_items)

    def persist_web_discovery_metadata(
        self,
        job_id: Optional[UUID],
        discovery_queries: list[str],
        ranked_sources: list[dict],
        knowledge: dict,
    ) -> dict:
        if not discovery_queries or not ranked_sources:
            return {"skipped": True}

        summary = {
            "queries": discovery_queries,
            "features": knowledge.get("features", []),
            "entities": knowledge.get("entities", []),
            "sources": [{"url": r.get("url"), "trust_score": r.get("trust_score")} for r in ranked_sources[:10]],
        }
        if job_id is None or not all(hasattr(self.db, attr) for attr in ["add", "commit", "refresh"]):
            return {"skipped": False, "run_id": None, "summary": summary}

        run = WebDiscoveryRun(
            job_id=job_id,
            query=discovery_queries[0],
            status="completed",
            discovered_count=len(ranked_sources),
            summary=summary,
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)

        for result in ranked_sources[: self.settings.max_web_results]:
            self.db.add(
                WebSource(
                    discovery_run_id=run.id,
                    url=result.get("url", ""),
                    title=result.get("title"),
                    source_type=result.get("source_type", "web"),
                    trust_score=float(result.get("trust_score", 0.0)),
                    metadata_json={
                        "snippet": result.get("snippet", ""),
                        "rank": result.get("rank"),
                        "rank_score": result.get("rank_score"),
                        "query": result.get("search_query"),
                    },
                )
            )
        self.db.commit()

        return {"skipped": False, "run_id": str(run.id), "summary": summary}

    def optionally_index_web_knowledge_into_rag(
        self,
        discovery_decision: dict,
        knowledge: dict,
        module_type: str,
        tags: list[str],
    ) -> dict:
        if not discovery_decision.get("should_run"):
            return {"attempted": False, "indexed_documents": 0}

        ingestion = self.ingestor.ingest_documents(knowledge.get("docs_for_rag", []), module_type, tags, "web_discovery")
        return {"attempted": True, **ingestion}

    def summarize_web_discovery(
        self,
        discovery_decision: dict,
        discovery_queries: list[str],
        ranked_sources: list[dict],
        knowledge: dict,
        persisted_discovery: dict,
        rag_ingestion: dict,
    ) -> dict:
        return {
            "used": bool(discovery_decision.get("should_run")),
            "reasons": discovery_decision.get("reasons", []),
            "queries": discovery_queries,
            "run_id": persisted_discovery.get("run_id"),
            "discovered_count": len(ranked_sources),
            "trusted_results": ranked_sources,
            "extracted_features": knowledge.get("features", []),
            "extracted_entities": knowledge.get("entities", []),
            "extracted_routes": knowledge.get("routes", []),
            "extracted_components": knowledge.get("components", []),
            "backend_patterns": knowledge.get("backend_patterns", []),
            "suggested_architecture": knowledge.get("suggested_architecture", []),
            "rag_ingestion": rag_ingestion,
        }

    def discover(
        self,
        query: str,
        job_id: Optional[UUID] = None,
        module_type: str = "general",
        tags: Optional[list[str]] = None,
    ) -> dict:
        tags = tags or []
        discovery_queries = [query]
        decision = {"should_run": True, "reasons": ["preview_or_direct_discovery"]}

        raw_results = self.search_web_sources(discovery_queries)
        trusted_results = self.filter_trusted_sources(raw_results)
        ranked_results = self.rank_trusted_sources(discovery_queries, trusted_results)
        fetched_payloads = self.fetch_shortlisted_sources(ranked_results, decision)
        knowledge = self.extract_structured_knowledge(ranked_results, fetched_payloads)
        persisted = self.persist_web_discovery_metadata(job_id, discovery_queries, ranked_results, knowledge)
        rag_ingestion = self.optionally_index_web_knowledge_into_rag(decision, knowledge, module_type, tags)
        summary = self.summarize_web_discovery(decision, discovery_queries, ranked_results, knowledge, persisted, rag_ingestion)

        return {
            "run_id": summary.get("run_id"),
            "query": query,
            "trusted_results": summary.get("trusted_results", []),
            "extracted_features": summary.get("extracted_features", []),
            "extracted_entities": summary.get("extracted_entities", []),
            "extracted_routes": summary.get("extracted_routes", []),
            "extracted_components": summary.get("extracted_components", []),
            "backend_patterns": summary.get("backend_patterns", []),
            "suggested_architecture": summary.get("suggested_architecture", []),
            "rag_ingestion": rag_ingestion,
            "summary": summary,
        }
