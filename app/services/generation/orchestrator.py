import json
import time
from pathlib import Path
from typing import Callable, Optional
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.constants import DEFAULT_DOMAIN, MANDATORY_OUTPUT_FILES, SUPPORTED_BACKENDS, SUPPORTED_FRONTENDS
from app.core.exceptions import GenerationException, ValidationException
from app.core.logging import get_logger
from app.core.security import sanitize_project_name
from app.models.project import Project
from app.services.caching.fingerprint import FingerprintService
from app.services.caching.generation_cache_service import GenerationCacheService
from app.services.generators.angular_generator import AngularGenerator
from app.services.generators.compose_generator import ComposeGenerator
from app.services.generators.docker_generator import DockerGenerator
from app.services.generators.readme_generator import ReadmeGenerator
from app.services.generators.springboot_generator import SpringBootGenerator
from app.services.generation.api_contract_builder import APIContractBuilder
from app.services.generation.manifest_builder import ManifestBuilder
from app.services.generation.pipeline import GenerationPipeline
from app.services.generation.project_assembler import ProjectAssembler
from app.services.generation.project_skeleton import ProjectSkeletonBuilder
from app.services.generation.project_spec_builder import ProjectSpecBuilder
from app.services.generation.prompt_debugger import PromptDebugger
from app.services.generation.prompt_parser import PromptParser
from app.services.generation.repair_engine import RepairEngine
from app.services.generation.validator import ProjectValidator
from app.services.generation.zip_packager import ZipPackager
from app.services.intelligence.domain_classifier import DomainClassifier
from app.services.intelligence.feature_expander import FeatureExpander
from app.services.intelligence.post_generation_indexer import PostGenerationIndexer
from app.services.intelligence.prompt_enricher import PromptEnricher
from app.services.llm.prompt_library import SYSTEM_PROMPT_ARCHITECT
from app.services.observability.metrics import CACHE_COUNTER, GENERATION_COUNTER, RAG_HISTOGRAM
from app.services.rag.retriever import RAGRetriever
from app.services.retrieval.base_project_selector import BaseProjectSelector
from app.services.retrieval.existing_project_search import ExistingProjectSearch
from app.services.retrieval.merge_engine import MergeEngine
from app.services.retrieval.project_adapter import ProjectAdapter
from app.services.retrieval.project_differ import ProjectDiffer
from app.services.web_discovery.discovery_decider import DiscoveryDecider
from app.services.web_discovery.web_discovery_orchestrator import WebDiscoveryOrchestrator
from app.utils.file_utils import ensure_directory

logger = get_logger(__name__)


class GenerationOrchestrator:
    STAGES = [
        "validate_request",
        "compute_fingerprint",
        "exact_cache_lookup",
        "parse_prompt",
        "classify_domain",
        "expand_features",
        "discover_existing_projects",
        "score_similarity",
        "select_execution_mode",
        "resolve_scaffold_strategy",
        "select_base_project",
        "retrieve_rag_context",
        "decide_if_web_discovery_needed",
        "build_discovery_queries",
        "search_web_sources",
        "filter_trusted_sources",
        "rank_trusted_sources",
        "fetch_shortlisted_sources",
        "extract_structured_knowledge",
        "persist_web_discovery_metadata",
        "optionally_index_web_knowledge_into_rag",
        "summarize_web_discovery",
        "build_project_spec",
        "build_api_contract",
        "build_manifest",
        "build_final_enriched_prompt",
        "persist_prompt_artifacts",
        "create_project_skeleton",
        "generate_backend_code",
        "generate_frontend_code",
        "generate_docker_files",
        "generate_readme",
        "assemble_project_files",
        "validate_structure",
        "validate_required_files",
        "validate_non_empty_files",
        "validate_manifest_consistency",
        "validate_path_safety",
        "optional_syntax_checks",
        "repair_if_needed",
        "revalidate_after_repair",
        "package_to_zip",
        "persist_project_metadata",
        "persist_generation_cache",
        "index_generated_project_into_rag",
        "finalize_job_status",
    ]

    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()

        self.prompt_parser = PromptParser()
        self.domain_classifier = DomainClassifier()
        self.feature_expander = FeatureExpander()
        self.project_spec_builder = ProjectSpecBuilder()
        self.api_contract_builder = APIContractBuilder()
        self.manifest_builder = ManifestBuilder()
        self.prompt_enricher_service = PromptEnricher()

        self.spring_generator = SpringBootGenerator()
        self.angular_generator = AngularGenerator()
        self.docker_generator = DockerGenerator()
        self.compose_generator = ComposeGenerator()
        self.readme_generator = ReadmeGenerator()

        self.assembler = ProjectAssembler()
        self.validator = ProjectValidator()
        self.repair_engine = RepairEngine()
        self.packager = ZipPackager()
        self.skeleton_builder = ProjectSkeletonBuilder()

        self.rag_retriever = RAGRetriever()
        self.post_generation_indexer = PostGenerationIndexer(db)

        self.fingerprint_service = FingerprintService()
        self.cache_service = GenerationCacheService(db)
        self.pipeline = GenerationPipeline()

        self.existing_search = ExistingProjectSearch(db)
        self.base_selector = BaseProjectSelector()
        self.project_differ = ProjectDiffer()
        self.project_adapter = ProjectAdapter()
        self.merge_engine = MergeEngine()
        self.web_discovery = WebDiscoveryOrchestrator(db)
        self.discovery_decider = DiscoveryDecider()

        self.prompt_debugger = PromptDebugger(db)

    def run(
        self,
        project_name: str,
        prompt: str,
        backend: str,
        frontend: str,
        features: list[str],
        progress_callback: Optional[Callable[[int, str], None]] = None,
        fingerprint: Optional[str] = None,
        trace_id: Optional[str] = None,
        job_id: Optional[UUID] = None,
        website_like: Optional[str] = None,
        mode_preference: str = "auto",
    ) -> dict:
        del trace_id
        logger.info(
            "[orchestrator] run start: project=%s backend=%s frontend=%s job_id=%s mode=%s",
            project_name, backend, frontend, job_id, mode_preference,
        )
        self.pipeline.stage_timings = {}
        stage_progress = self._stage_progress_map()

        try:
            self.pipeline.execute_stage(
                "validate_request",
                self.validate_request,
                progress_callback,
                stage_progress["validate_request"],
                backend,
                frontend,
                prompt,
                mode_preference,
            )

            safe_project_name = sanitize_project_name(project_name)
            project_id = uuid4()
            project_root = self._build_project_root(project_id, safe_project_name)
            zip_path = project_root.with_suffix(".zip")

            request_fingerprint = fingerprint or self.pipeline.execute_stage(
                "compute_fingerprint",
                self.compute_fingerprint,
                progress_callback,
                stage_progress["compute_fingerprint"],
                prompt,
                backend,
                frontend,
                features,
            )

            cached = self.pipeline.execute_stage(
                "exact_cache_lookup",
                self.exact_cache_lookup,
                progress_callback,
                stage_progress["exact_cache_lookup"],
                request_fingerprint,
            )
            if cached and cached.project_id:
                cached_project = self.db.query(Project).filter(Project.id == cached.project_id).first()
                if cached_project and Path(cached_project.zip_path).exists():
                    CACHE_COUNTER.labels(outcome="hit").inc()
                    GENERATION_COUNTER.labels(status="cached").inc()

                    parsed_for_cache = self.prompt_parser.parse_prompt(prompt)
                    if job_id:
                        self.prompt_debugger.persist_prompt_artifact(
                            job_id=job_id,
                            raw_user_prompt=prompt,
                            parsed_prompt=parsed_for_cache,
                            parsed_prompt_summary=self.build_parsed_prompt_summary(parsed_for_cache),
                            expanded_features=sorted(set(features)),
                            execution_mode="reuse",
                            rag_summary={"cache_hit": True},
                            rag_context_summary={},
                            web_discovery_summary={"used": False, "reasons": []},
                            adaptation_context_summary={},
                            trusted_sources=[],
                            pre_final_prompt=None,
                            final_enriched_prompt=(
                                "EXACT_CACHE_HIT\n"
                                f"fingerprint={request_fingerprint}\n"
                                f"project_id={cached_project.id}"
                            ),
                            system_prompt=SYSTEM_PROMPT_ARCHITECT,
                        )

                    cached_result = self.build_reused_result(
                        project=cached_project,
                        request_fingerprint=request_fingerprint,
                        execution_mode="reuse",
                        cache_hit=True,
                    )
                    return self.pipeline.execute_stage(
                        "finalize_job_status",
                        self.finalize_job_status,
                        progress_callback,
                        stage_progress["finalize_job_status"],
                        cached_result,
                        project_root=None,
                        artifact=None,
                        cache_result={"hit": True},
                        indexing_result={"skipped": True},
                    )

            CACHE_COUNTER.labels(outcome="miss").inc()

            parsed_prompt = self.pipeline.execute_stage(
                "parse_prompt",
                self.parse_prompt,
                progress_callback,
                stage_progress["parse_prompt"],
                prompt,
            )
            domain = self.pipeline.execute_stage(
                "classify_domain",
                self.classify_domain,
                progress_callback,
                stage_progress["classify_domain"],
                parsed_prompt,
            )
            expanded_features = self.pipeline.execute_stage(
                "expand_features",
                self.expand_features,
                progress_callback,
                stage_progress["expand_features"],
                parsed_prompt,
                features,
                domain,
            )
            existing_projects = self.pipeline.execute_stage(
                "discover_existing_projects",
                self.discover_existing_projects,
                progress_callback,
                stage_progress["discover_existing_projects"],
                domain,
            )
            scored_candidates = self.pipeline.execute_stage(
                "score_similarity",
                self.score_similarity,
                progress_callback,
                stage_progress["score_similarity"],
                prompt,
                expanded_features,
                existing_projects,
            )
            execution = self.pipeline.execute_stage(
                "select_execution_mode",
                self.select_execution_mode,
                progress_callback,
                stage_progress["select_execution_mode"],
                mode_preference,
                scored_candidates,
            )
            scaffold_strategy = self.pipeline.execute_stage(
                "resolve_scaffold_strategy",
                self.resolve_scaffold_strategy,
                progress_callback,
                stage_progress["resolve_scaffold_strategy"],
                domain,
                execution,
            )
            selected_base = self.pipeline.execute_stage(
                "select_base_project",
                self.select_base_project,
                progress_callback,
                stage_progress["select_base_project"],
                execution,
            )
            rag_context = self.pipeline.execute_stage(
                "retrieve_rag_context",
                self.retrieve_rag_context,
                progress_callback,
                stage_progress["retrieve_rag_context"],
                prompt,
                domain,
                expanded_features,
                selected_base,
            )
            rag_context_summary = self.build_rag_context_summary(rag_context)

            discovery_decision = self.pipeline.execute_stage(
                "decide_if_web_discovery_needed",
                self.decide_if_web_discovery_needed,
                progress_callback,
                stage_progress["decide_if_web_discovery_needed"],
                prompt,
                domain,
                website_like,
                execution,
                rag_context_summary,
            )
            discovery_queries = self.pipeline.execute_stage(
                "build_discovery_queries",
                self.build_discovery_queries,
                progress_callback,
                stage_progress["build_discovery_queries"],
                prompt,
                domain,
                website_like,
                expanded_features,
                discovery_decision,
            )
            raw_web_sources = self.pipeline.execute_stage(
                "search_web_sources",
                self.search_web_sources,
                progress_callback,
                stage_progress["search_web_sources"],
                discovery_queries,
            )
            trusted_sources = self.pipeline.execute_stage(
                "filter_trusted_sources",
                self.filter_trusted_sources,
                progress_callback,
                stage_progress["filter_trusted_sources"],
                raw_web_sources,
            )
            ranked_sources = self.pipeline.execute_stage(
                "rank_trusted_sources",
                self.rank_trusted_sources,
                progress_callback,
                stage_progress["rank_trusted_sources"],
                discovery_queries,
                trusted_sources,
            )
            fetched_sources = self.pipeline.execute_stage(
                "fetch_shortlisted_sources",
                self.fetch_shortlisted_sources,
                progress_callback,
                stage_progress["fetch_shortlisted_sources"],
                ranked_sources,
                discovery_decision,
            )
            extracted_knowledge = self.pipeline.execute_stage(
                "extract_structured_knowledge",
                self.extract_structured_knowledge,
                progress_callback,
                stage_progress["extract_structured_knowledge"],
                ranked_sources,
                fetched_sources,
            )
            persisted_discovery = self.pipeline.execute_stage(
                "persist_web_discovery_metadata",
                self.persist_web_discovery_metadata,
                progress_callback,
                stage_progress["persist_web_discovery_metadata"],
                job_id,
                discovery_queries,
                ranked_sources,
                extracted_knowledge,
            )
            rag_ingestion = self.pipeline.execute_stage(
                "optionally_index_web_knowledge_into_rag",
                self.optionally_index_web_knowledge_into_rag,
                progress_callback,
                stage_progress["optionally_index_web_knowledge_into_rag"],
                discovery_decision,
                extracted_knowledge,
                domain,
                expanded_features,
            )
            web_discovery_summary = self.pipeline.execute_stage(
                "summarize_web_discovery",
                self.summarize_web_discovery,
                progress_callback,
                stage_progress["summarize_web_discovery"],
                discovery_decision,
                discovery_queries,
                ranked_sources,
                extracted_knowledge,
                persisted_discovery,
                rag_ingestion,
            )

            adaptation_context_summary = self.build_adaptation_context(
                execution_mode=execution["mode"],
                selected_base=selected_base,
                prompt=prompt,
                expanded_features=expanded_features,
                website_like=website_like,
            )

            if execution["mode"] == "reuse" and selected_base and Path(selected_base.zip_path).exists():
                if job_id:
                    self.pipeline.execute_stage(
                        "persist_prompt_artifacts",
                        self.persist_prompt_artifacts,
                        progress_callback,
                        stage_progress["persist_prompt_artifacts"],
                        job_id,
                        prompt,
                        parsed_prompt,
                        expanded_features,
                        execution["mode"],
                        rag_context_summary,
                        web_discovery_summary,
                        adaptation_context_summary,
                        ranked_sources,
                        None,
                        self.merge_engine.merge_contexts(
                            base_enriched_prompt=(
                                "REUSE_SELECTION\n"
                                f"selected_project_id={selected_base.id}\n"
                                f"selection_score={execution['score']}"
                            ),
                            adaptation_context=adaptation_context_summary,
                            web_discovery_summary=web_discovery_summary,
                        ),
                    )

                reused_result = self.build_reused_result(
                    project=selected_base,
                    request_fingerprint=request_fingerprint,
                    execution_mode="reuse",
                    cache_hit=False,
                    selection_score=execution["score"],
                    selection_candidates=execution["candidates"],
                )
                return self.pipeline.execute_stage(
                    "finalize_job_status",
                    self.finalize_job_status,
                    progress_callback,
                    stage_progress["finalize_job_status"],
                    reused_result,
                    project_root=None,
                    artifact=None,
                    cache_result={"hit": False, "reused": True},
                    indexing_result={"skipped": True},
                )

            project_spec = self.pipeline.execute_stage(
                "build_project_spec",
                self.build_project_spec,
                progress_callback,
                stage_progress["build_project_spec"],
                parsed_prompt,
                safe_project_name,
                backend,
                frontend,
                expanded_features,
                domain,
                execution,
                scaffold_strategy,
                selected_base,
                web_discovery_summary,
            )
            api_contract = self.pipeline.execute_stage(
                "build_api_contract",
                self.build_api_contract,
                progress_callback,
                stage_progress["build_api_contract"],
                project_spec,
            )
            manifest = self.pipeline.execute_stage(
                "build_manifest",
                self.build_manifest,
                progress_callback,
                stage_progress["build_manifest"],
                project_spec,
                api_contract,
            )
            prompt_payload = self.pipeline.execute_stage(
                "build_final_enriched_prompt",
                self.build_final_enriched_prompt,
                progress_callback,
                stage_progress["build_final_enriched_prompt"],
                prompt,
                project_spec,
                api_contract,
                rag_context,
                scaffold_strategy,
                execution,
                web_discovery_summary,
                adaptation_context_summary,
            )
            artifact = self.pipeline.execute_stage(
                "persist_prompt_artifacts",
                self.persist_prompt_artifacts,
                progress_callback,
                stage_progress["persist_prompt_artifacts"],
                job_id,
                prompt,
                parsed_prompt,
                expanded_features,
                execution["mode"],
                rag_context_summary,
                web_discovery_summary,
                adaptation_context_summary,
                ranked_sources,
                prompt_payload["pre_final_prompt"],
                prompt_payload["final_enriched_prompt"],
            )

            self.pipeline.execute_stage(
                "create_project_skeleton",
                self.create_project_skeleton,
                progress_callback,
                stage_progress["create_project_skeleton"],
                project_root,
                project_id,
            )
            backend_files = self.pipeline.execute_stage(
                "generate_backend_code",
                self.generate_backend_code,
                progress_callback,
                stage_progress["generate_backend_code"],
                project_spec,
                api_contract,
                rag_context,
            )
            frontend_files = self.pipeline.execute_stage(
                "generate_frontend_code",
                self.generate_frontend_code,
                progress_callback,
                stage_progress["generate_frontend_code"],
                project_spec,
                api_contract,
                rag_context,
            )

            # LLM-powered code improvement step for frontend files
            from app.services.llm.openai_provider import OpenAIProvider
            llm = OpenAIProvider()

            features_str = ", ".join(project_spec.get("features", []))
            domain = project_spec.get("domain", "web application")

            def _build_llm_prompt(file_path: str, file_content: str) -> str:
                if file_path.endswith(".css"):
                    return (
                        f"User prompt: {prompt}\n"
                        f"Domain: {domain}\n"
                        f"Features: {features_str}\n"
                        f"File: {file_path}\n"
                        f"Current CSS:\n{file_content}\n\n"
                        "You are an expert UI/UX designer and CSS engineer. "
                        "Completely rewrite this CSS file to produce a STUNNING, MODERN, PRODUCTION-READY design. "
                        "Requirements:\n"
                        "- Use CSS custom properties (variables) for theming\n"
                        "- Apply a beautiful color palette matching the domain/brand\n"
                        "- Add smooth transitions, hover effects, box shadows, and gradients\n"
                        "- Make it fully responsive (mobile, tablet, desktop) with media queries\n"
                        "- Style all interactive elements (buttons, inputs, cards, navbars, modals)\n"
                        "- Use flexbox and grid for clean layouts\n"
                        "- Add professional typography with proper font sizes and weights\n"
                        "- Include loading states, error states, and empty states styling\n"
                        "- Ensure accessibility with focus states and contrast ratios\n"
                        "Return ONLY the CSS code, no markdown fences, no explanations."
                    )
                elif file_path.endswith(".html"):
                    return (
                        f"User prompt: {prompt}\n"
                        f"Domain: {domain}\n"
                        f"Features: {features_str}\n"
                        f"File: {file_path}\n"
                        f"Current HTML/Angular template:\n{file_content}\n\n"
                        "You are an expert Angular developer and UI designer. "
                        "Rewrite this Angular HTML template with a MODERN, PROFESSIONAL UI. "
                        "Requirements:\n"
                        "- Use Angular Material components wherever appropriate\n"
                        "- Add semantic HTML5 elements\n"
                        "- Include all features from the user prompt\n"
                        "- Add proper loading spinners, error messages, empty state messages\n"
                        "- Use Angular directives (*ngIf, *ngFor) correctly\n"
                        "- Ensure all buttons, forms, and interactive elements are styled\n"
                        "- Add accessibility attributes (aria-labels, roles)\n"
                        "Return ONLY the Angular HTML code, no markdown fences, no explanations."
                    )
                else:  # .ts
                    return (
                        f"User prompt: {prompt}\n"
                        f"Domain: {domain}\n"
                        f"Features: {features_str}\n"
                        f"File: {file_path}\n"
                        f"Current TypeScript:\n{file_content}\n\n"
                        "You are an expert Angular developer. "
                        "Rewrite or improve this TypeScript file to include all features from the prompt. "
                        "Follow Angular best practices, use RxJS, typed interfaces, and proper error handling. "
                        "Return ONLY the TypeScript code, no markdown fences, no explanations."
                    )

            # Files that define the app structure — must NOT be rewritten by LLM
            # because they import only what the generator actually creates.
            LLM_SKIP_FILES = {
                "frontend/src/app/app-routing.module.ts",
                "frontend/src/app/app.module.ts",
                "frontend/src/app/app.component.ts",
                "frontend/src/main.ts",
                "frontend/src/index.html",
            }

            # Pass 1: LLM improvement per file (skip structural files)
            for file_path, file_content in list(frontend_files.items()):
                if file_path in LLM_SKIP_FILES:
                    continue
                if file_path.endswith((".html", ".css", ".ts")):
                    llm_prompt = _build_llm_prompt(file_path, file_content)
                    improved_content = llm.generate_code_block(prompt=llm_prompt, language="text")
                    if improved_content and improved_content.strip():
                        frontend_files[file_path] = improved_content

            # Pass 2: LLM review/rework — verify all files are consistent and production-ready
            all_frontend_summary = "\n\n".join(
                f"=== {fp} ===\n{fc[:800]}" for fp, fc in frontend_files.items()
                if fp.endswith((".html", ".css", ".ts")) and fp not in LLM_SKIP_FILES
            )
            review_prompt = (
                f"User prompt: {prompt}\n"
                f"Domain: {domain}\n"
                f"Features: {features_str}\n\n"
                "You are a senior software architect doing a final review of the following Angular project files. "
                "Check each file for:\n"
                "1. CSS files: Are they visually impressive, responsive, and production-quality? If not, rewrite them.\n"
                "2. HTML files: Do they match the user prompt features and use proper Angular/Material? If not, fix them.\n"
                "3. TypeScript files: Are they complete, typed, and error-free? If not, fix them.\n\n"
                "Return a JSON object where keys are file paths and values are the corrected file contents. "
                "Only include files that needed changes. Return valid JSON only, no markdown.\n\n"
                f"Files to review:\n{all_frontend_summary}"
            )
            try:
                review_result = llm.generate_structured_json(prompt=review_prompt)
                if isinstance(review_result, dict):
                    for fp, fc in review_result.items():
                        if fp in LLM_SKIP_FILES:
                            continue  # never allow LLM to overwrite structural files
                        if fp in frontend_files and fc and str(fc).strip():
                            frontend_files[fp] = str(fc)
                            logger.info("LLM review pass improved file: %s", fp)
            except Exception:
                logger.warning("LLM review pass failed, continuing with pass-1 results", exc_info=True)

            import subprocess
            import os
            import re as _re
            MAX_TEST_FIX_ATTEMPTS = 3

            # ── Step A: Resolve missing imports ──────────────────────────────────
            # Scan all .ts files for import paths. If any imported file is not in
            # frontend_files, generate it with the LLM so the build doesn't fail.
            def _relative_to_frontend(base_fp: str, rel_import: str) -> str:
                """Resolve a relative import path to a frontend_files key."""
                base_dir = "/".join(base_fp.split("/")[:-1])
                parts = base_dir.split("/")
                for seg in rel_import.split("/"):
                    if seg == "..":
                        parts = parts[:-1]
                    elif seg != ".":
                        parts.append(seg)
                return "/".join(parts) + ".ts"

            known_files = set(frontend_files.keys())
            for fp, fc in list(frontend_files.items()):
                if not fp.endswith(".ts"):
                    continue
                for match in _re.finditer(r"from\s+['\"](\./[^'\"]+|\.{2}/[^'\"]+)['\"]", fc):
                    rel = match.group(1)
                    resolved = _relative_to_frontend(fp, rel)
                    if resolved not in known_files:
                        gen_prompt = (
                            f"User prompt: {prompt}\nDomain: {domain}\nFeatures: {features_str}\n\n"
                            f"The file '{fp}' imports from '{rel}' which resolves to '{resolved}'.\n"
                            f"Generate the complete Angular TypeScript file for '{resolved}'. "
                            "Include the @Component/@Injectable decorator, proper imports, typed interfaces, "
                            "and full implementation matching the domain and features. "
                            "Return ONLY the TypeScript code, no markdown fences."
                        )
                        generated = llm.generate_code_block(prompt=gen_prompt, language="typescript")
                        if generated and generated.strip():
                            frontend_files[resolved] = generated
                            known_files.add(resolved)
                            logger.info("LLM generated missing file: %s", resolved)

            # ── Step B: Skeleton / placeholder content ───────────────────────────
            # If website_like is provided, inject realistic placeholder data so the
            # project looks like a real running website, not an empty shell.
            if website_like:
                skeleton_prompt = (
                    f"User prompt: {prompt}\n"
                    f"Reference website: {website_like}\n"
                    f"Domain: {domain}\nFeatures: {features_str}\n\n"
                    "The generated Angular project may have empty/placeholder content. "
                    "Generate realistic, production-quality placeholder data for this project:\n"
                    "1. A TypeScript file 'frontend/src/app/core/mock-data.ts' with exported const arrays "
                    "   of 10-20 realistic mock items (products, users, orders etc.) matching the domain. "
                    "   Use placeholder images from 'https://picsum.photos/seed/{id}/400/300'. "
                    "2. An Angular service file 'frontend/src/app/core/services/mock.service.ts' that "
                    "   returns these mock items as Observables (use 'of()' from rxjs). "
                    "3. Update the main feature component HTML to display this data with *ngFor, "
                    "   Angular Material cards, and skeleton loading (mat-progress-bar while loading).\n"
                    "Return a JSON object: {filepath: fileContent}. Valid JSON only, no markdown."
                )
                try:
                    skeleton_result = llm.generate_structured_json(prompt=skeleton_prompt)
                    if isinstance(skeleton_result, dict):
                        for fp, fc in skeleton_result.items():
                            if fc and str(fc).strip() and fp not in LLM_SKIP_FILES:
                                frontend_files[fp] = str(fc)
                                logger.info("Skeleton content injected: %s", fp)
                except Exception:
                    logger.warning("Skeleton content generation failed, continuing", exc_info=True)

            # ── Step C: Write all frontend files to disk ──────────────────────────
            for fp, fc in frontend_files.items():
                abs_path = os.path.join(str(project_root), fp)
                os.makedirs(os.path.dirname(abs_path), exist_ok=True)
                with open(abs_path, "w") as f:
                    f.write(fc)

            # ── Step D: Angular build validation + LLM fix loop ──────────────────
            # Run ng build to check for real TypeScript/Angular compilation errors.
            # If errors found, send them + the broken files to LLM for correction.
            frontend_dir = os.path.join(str(project_root), "frontend")
            _node_modules = os.path.join(frontend_dir, "node_modules")
            if os.path.exists(frontend_dir) and not os.path.exists(_node_modules):
                try:
                    subprocess.run(["npm", "install", "--legacy-peer-deps"],
                                   cwd=frontend_dir, capture_output=True, timeout=180)
                except Exception:
                    pass

            _build_succeeded = False
            for attempt in range(MAX_TEST_FIX_ATTEMPTS):
                if not os.path.exists(os.path.join(frontend_dir, "node_modules")):
                    break
                try:
                    build_result = subprocess.run(
                        ["npx", "ng", "build", "--configuration=development", "--no-progress"],
                        cwd=frontend_dir, capture_output=True, text=True, timeout=300
                    )
                except Exception:
                    break
                if build_result.returncode == 0:
                    logger.info("Angular build succeeded on attempt %d", attempt + 1)
                    _build_succeeded = True
                    break

                # Parse errors: extract "Error: src/app/..." lines
                error_output = build_result.stderr + "\n" + build_result.stdout
                error_lines = [l for l in error_output.splitlines()
                               if ("Error:" in l or "error TS" in l or "error NG" in l)]
                if not error_lines:
                    break

                # Collect the broken files referenced in errors
                broken_fps = set()
                for el in error_lines:
                    m = _re.search(r"src/[^\s:]+\.ts", el)
                    if m:
                        broken_fps.add("frontend/" + m.group(0))

                broken_contents = {
                    fp: frontend_files[fp]
                    for fp in broken_fps if fp in frontend_files
                }
                _error_summary = "\n".join(error_lines[:40])
                _available_pkgs: list[str] = []
                try:
                    with open(os.path.join(frontend_dir, "package.json")) as _pf:
                        _pkg_data = json.loads(_pf.read())
                    _available_pkgs = (
                        list(_pkg_data.get("dependencies", {}).keys())
                        + list(_pkg_data.get("devDependencies", {}).keys())
                    )
                except Exception:
                    pass
                _pkg_constraint = (
                    "AVAILABLE npm packages (ONLY use these, NEVER import anything else): "
                    + ", ".join(sorted(_available_pkgs)) + "\n"
                    if _available_pkgs else ""
                )
                fix_prompt = (
                    f"User prompt: {prompt}\nDomain: {domain}\nFeatures: {features_str}\n\n"
                    + _pkg_constraint
                    + (
                        "The Angular project failed to compile. Fix ALL errors so `ng build` succeeds.\n"
                        "RULES:\n"
                        "- Only import files that exist in the provided file list\n"
                        "- Do NOT add new component imports to app-routing or app.module\n"
                        "- Fix TypeScript strict errors (add '!' or '| undefined', initialize properties)\n"
                        "- Remove any 'window[\"ngRef\"]' usage in main.ts\n"
                        "- Return a JSON object {filepath: corrected_content} for ONLY the files that need fixing.\n\n"
                        f"Build errors:\n{_error_summary}\n\n"
                        f"Broken files:\n"
                    )
                    + "\n\n".join(f"=== {fp} ===\n{fc}" for fp, fc in broken_contents.items())
                )
                try:
                    fix_result = llm.generate_structured_json(prompt=fix_prompt)
                    if isinstance(fix_result, dict):
                        for fp, fc in fix_result.items():
                            if fp in LLM_SKIP_FILES and attempt < MAX_TEST_FIX_ATTEMPTS - 1:
                                continue
                            if fc and str(fc).strip():
                                frontend_files[fp] = str(fc)
                                abs_path = os.path.join(str(project_root), fp)
                                os.makedirs(os.path.dirname(abs_path), exist_ok=True)
                                with open(abs_path, "w") as fh:
                                    fh.write(str(fc))
                                logger.info("LLM build-fix applied: %s (attempt %d)", fp, attempt + 1)
                except Exception:
                    logger.warning("LLM build-fix pass failed on attempt %d", attempt + 1, exc_info=True)

            # --- Automated Test Generation and LLM Test-Fix Loop ---
            # 1. Generate tests for backend and frontend
            from app.services.llm.openai_provider import OpenAIProvider
            llm_test = OpenAIProvider()
            MAX_TEST_FIX_ATTEMPTS = 3

            def _generate_tests_for_file(file_path, file_content):
                if file_path.endswith(".ts") and not file_path.endswith(".spec.ts"):
                    prompt = (
                        f"Write a comprehensive Angular unit test (.spec.ts) for the following file. "
                        f"Use Jasmine and TestBed. Return ONLY the .spec.ts code.\n\n{file_content}"
                    )
                    return llm_test.generate_code_block(prompt=prompt, language="typescript")
                elif file_path.endswith(".py") and "/app/" in file_path:
                    prompt = (
                        f"Write a comprehensive pytest test file for the following Python module. "
                        f"Return ONLY the test code.\n\n{file_content}"
                    )
                    return llm_test.generate_code_block(prompt=prompt, language="python")
                return None

            # Generate frontend tests
            for file_path, file_content in list(frontend_files.items()):
                if file_path.endswith(".ts") and not file_path.endswith(".spec.ts"):
                    test_code = _generate_tests_for_file(file_path, file_content)
                    if test_code and test_code.strip():
                        test_path = file_path.replace(".ts", ".spec.ts")
                        frontend_files[test_path] = test_code

            # Generate backend tests
            for file_path, file_content in list(backend_files.items()):
                if file_path.endswith(".py") and "/app/" in file_path:
                    test_code = _generate_tests_for_file(file_path, file_content)
                    if test_code and test_code.strip():
                        test_path = file_path.replace("/app/", "/tests/test_")
                        if not test_path.endswith(".py"):
                            test_path += ".py"
                        backend_files[test_path] = test_code

            # Generate frontend tests
            for file_path, file_content in list(frontend_files.items()):
                if file_path.endswith(".ts") and not file_path.endswith(".spec.ts") and file_path not in LLM_SKIP_FILES:
                    test_code = _generate_tests_for_file(file_path, file_content)
                    if test_code and test_code.strip():
                        test_path = file_path.replace(".ts", ".spec.ts")
                        frontend_files[test_path] = test_code

            # 3. Run backend tests (pytest)
            for attempt in range(MAX_TEST_FIX_ATTEMPTS):
                backend_test_result = subprocess.run([
                    "pytest", os.path.join(str(project_root), "tests")
                ], capture_output=True, text=True)
                if backend_test_result.returncode == 0:
                    break
                # If failed, ask LLM to fix code
                fail_prompt = (
                    "The following pytest tests failed. Fix the code so all tests pass. "
                    "Return only the corrected code files as a JSON object: {filepath: content}.\n"
                    f"Test output:\n{backend_test_result.stdout}\n"
                )
                fix_result = llm_test.generate_structured_json(prompt=fail_prompt)
                if isinstance(fix_result, dict):
                    for fp, fc in fix_result.items():
                        abs_path = os.path.join(str(project_root), fp)
                        with open(abs_path, "w") as f:
                            f.write(fc)
                        backend_files[fp] = fc
            # 4. Run frontend tests (ng test --watch=false)
            for attempt in range(MAX_TEST_FIX_ATTEMPTS):
                try:
                    frontend_test_result = subprocess.run([
                        "npx", "ng", "test", "--watch=false", "--browsers=ChromeHeadless"
                    ], cwd=os.path.join(str(project_root), "frontend"), capture_output=True, text=True)
                except Exception as e:
                    break
                if frontend_test_result.returncode == 0:
                    break
                fail_prompt = (
                    "The following Angular tests failed. Fix the code so all tests pass. "
                    "Return only the corrected code files as a JSON object: {filepath: content}.\n"
                    f"Test output:\n{frontend_test_result.stdout}\n"
                )
                fix_result = llm_test.generate_structured_json(prompt=fail_prompt)
                if isinstance(fix_result, dict):
                    for fp, fc in fix_result.items():
                        abs_path = os.path.join(str(project_root), fp)
                        with open(abs_path, "w") as f:
                            f.write(fc)
                        frontend_files[fp] = fc

            # --- End Automated Test Generation and LLM Test-Fix Loop ---

            # ══════════════════════════════════════════════════════════════════════
            # PASS 3 — Full-Site Enhancement: multi-page, realistic, production-ready
            # ══════════════════════════════════════════════════════════════════════
            # This pass turns the generated single-page skeleton into a FULL website
            # with multiple pages, rich navigation, realistic data, and a polished UI
            # that mirrors the reference website (website_like) if provided.
            try:
                # Build a map of existing files for context
                _existing_summary = "\n".join(
                    f"  {fp}" for fp in sorted(frontend_files.keys())
                    if fp.endswith((".ts", ".html", ".css"))
                )
                _website_context = (
                    f"Reference website to mirror: {website_like}" if website_like
                    else "No reference website — create a professional, production-quality site."
                )

                enhancement_prompt = (
                    f"User prompt: {prompt}\n"
                    f"Domain: {domain}\n"
                    f"Features: {features_str}\n"
                    f"{_website_context}\n\n"
                    "You are a senior full-stack Angular developer. "
                    "The project currently has these files:\n"
                    f"{_existing_summary}\n\n"
                    "Your job is to COMPLETELY ENHANCE this project into a FULL, REALISTIC, PRODUCTION-READY website. "
                    "Requirements:\n\n"
                    "1. MULTIPLE PAGES: Generate separate routed Angular components for every major section "
                    "   (e.g. Home, Products/Listing, Product Detail, Cart, Checkout, Auth/Login, Admin Dashboard, "
                    "   Profile, Orders — whatever fits the domain). Each must be a standalone .ts + .html + .css.\n\n"
                    "2. REAL NAVIGATION: Update app-routing.module.ts with all new routes. "
                    "   Create a full navbar component (frontend/src/app/shared/navbar/navbar.component.ts/.html/.css) "
                    "   with logo, links to all pages, search bar, user/cart icons, and mobile hamburger menu.\n\n"
                    "3. REALISTIC DATA: Every page must display real-looking content — NOT 'Lorem ipsum'. "
                    "   Use domain-appropriate text, product/item names, prices, descriptions. "
                    "   For images use: https://picsum.photos/seed/{seed}/400/300 with unique seeds per item.\n\n"
                    "4. HERO SECTION: The home page must have a stunning hero banner with headline, "
                    "   subheading, CTA button, and a background image/gradient matching the domain brand.\n\n"
                    "5. FEATURE SECTIONS: Category grids, featured items/cards, testimonials, stats, "
                    "   call-to-action sections — whatever makes the domain look complete and credible.\n\n"
                    "6. FOOTER: A full footer with logo, links, social icons, and copyright.\n\n"
                    "7. SHARED SERVICES: Generate all necessary Angular services "
                    "   (auth.service.ts, product.service.ts, cart.service.ts etc.) with proper "
                    "   TypeScript interfaces and BehaviorSubject/Observable state management.\n\n"
                    "8. MODELS: Generate TypeScript model interfaces in frontend/src/app/models/ "
                    "   (product.model.ts, user.model.ts, order.model.ts etc.).\n\n"
                    "9. APP MODULE: Update app.module.ts to declare ALL new components and import "
                    "   all needed Angular Material modules, FormsModule, ReactiveFormsModule, HttpClientModule.\n\n"
                    "10. CSS QUALITY: Every component CSS must be production-quality — "
                    "    CSS variables, gradients, animations, hover effects, fully responsive.\n\n"
                    "CRITICAL RULES:\n"
                    "- Return a single JSON object: {\"filepath\": \"complete file content\"}\n"
                    "- Include ALL files: every .ts, .html, and .css for every component\n"
                    "- Every import path must be correct and resolvable\n"
                    "- No TypeScript strict errors — initialize all properties\n"
                    "- Return valid JSON only, no markdown fences or explanations\n"
                    "- Generate at minimum 8-12 components, 2-3 services, 3-5 models"
                )

                logger.info("Pass 3: Starting full-site enhancement LLM pass")
                if not _build_succeeded:
                    logger.warning("Pass 3: Skipping LLM enhancement call — build has unresolved errors")
                    enhancement_result = {}
                else:
                    enhancement_result = llm.generate_structured_json(
                        prompt=enhancement_prompt, max_tokens=16000
                    )

                if isinstance(enhancement_result, dict) and enhancement_result:
                    enhanced_count = 0
                    for fp, fc in enhancement_result.items():
                        if not fp or not fc or not str(fc).strip():
                            continue
                        # Normalise path — strip leading slashes
                        fp = fp.lstrip("/")
                        if not fp.startswith("frontend/"):
                            fp = "frontend/" + fp
                        frontend_files[fp] = str(fc)
                        # Write to disk immediately
                        abs_path = os.path.join(str(project_root), fp)
                        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
                        with open(abs_path, "w") as _fh:
                            _fh.write(str(fc))
                        enhanced_count += 1
                    logger.info("Pass 3: Enhancement applied %d files", enhanced_count)

                    # Pass 3B — Post-enhancement build fix (up to 2 more attempts)
                    for _attempt in range(2):
                        if not os.path.exists(os.path.join(frontend_dir, "node_modules")):
                            break
                        try:
                            _build = subprocess.run(
                                ["npx", "ng", "build", "--configuration=development", "--no-progress"],
                                cwd=frontend_dir, capture_output=True, text=True, timeout=300
                            )
                        except Exception:
                            break
                        if _build.returncode == 0:
                            logger.info("Pass 3B: Build succeeded after enhancement (attempt %d)", _attempt + 1)
                            break
                        _err_out = _build.stderr + "\n" + _build.stdout
                        _err_lines = [l for l in _err_out.splitlines()
                                      if "Error:" in l or "error TS" in l or "error NG" in l]
                        if not _err_lines:
                            break
                        _broken = {}
                        for _el in _err_lines:
                            _m = _re.search(r"src/[^\s:]+\.ts", _el)
                            if _m:
                                _fp = "frontend/" + _m.group(0)
                                if _fp in frontend_files:
                                    _broken[_fp] = frontend_files[_fp]
                        _err_summary = "\n".join(_err_lines[:50])
                        _fix_p = (
                            f"User prompt: {prompt}\nDomain: {domain}\n\n"
                            "Fix these Angular build errors. Return JSON {filepath: content} for broken files only.\n"
                            "Rules: fix TypeScript strict errors, correct import paths, "
                            "initialize all class properties, do not invent new files.\n\n"
                            f"Errors:\n{_err_summary}\n\n"
                            "Broken files:\n" +
                            "\n\n".join(f"=== {_fp} ===\n{_fc[:1500]}" for _fp, _fc in _broken.items())
                        )
                        try:
                            _fix_r = llm.generate_structured_json(prompt=_fix_p)
                            if isinstance(_fix_r, dict):
                                for _fp, _fc in _fix_r.items():
                                    if _fc and str(_fc).strip():
                                        _fp = _fp.lstrip("/")
                                        if not _fp.startswith("frontend/"):
                                            _fp = "frontend/" + _fp
                                        frontend_files[_fp] = str(_fc)
                                        _abs = os.path.join(str(project_root), _fp)
                                        os.makedirs(os.path.dirname(_abs), exist_ok=True)
                                        with open(_abs, "w") as _fh:
                                            _fh.write(str(_fc))
                                        logger.info("Pass 3B fix: %s", _fp)
                        except Exception:
                            logger.warning("Pass 3B build-fix failed on attempt %d", _attempt + 1, exc_info=True)
                else:
                    logger.warning("Pass 3: Enhancement returned no results, keeping existing files")
            except Exception:
                logger.warning("Pass 3 enhancement failed, continuing with existing files", exc_info=True)
            # ══════════════════════════════════════════════════════════════════════
            # END PASS 3
            # ══════════════════════════════════════════════════════════════════════

            docker_files = self.pipeline.execute_stage(
                "generate_docker_files",
                self.generate_docker_files,
                progress_callback,
                stage_progress["generate_docker_files"],
                project_spec,
                api_contract,
                rag_context,
            )
            readme_files = self.pipeline.execute_stage(
                "generate_readme",
                self.generate_readme,
                progress_callback,
                stage_progress["generate_readme"],
                project_spec,
                api_contract,
                manifest,
            )

            assembled_files_payload = {
                **backend_files,
                **frontend_files,
                **docker_files,
                **self.compose_generator.generate(project_spec, api_contract, rag_context),
                **readme_files,
                **self.build_prompt_files_payload(
                    job_id=job_id,
                    project_id=project_id,
                    prompt=prompt,
                    parsed_prompt=parsed_prompt,
                    expanded_features=expanded_features,
                    execution_mode=execution["mode"],
                    rag_context_summary=rag_context_summary,
                    web_discovery_summary=web_discovery_summary,
                    adaptation_context_summary=adaptation_context_summary,
                    ranked_sources=ranked_sources,
                    prompt_payload=prompt_payload,
                ),
            }
            generated_files = self.pipeline.execute_stage(
                "assemble_project_files",
                self.assemble_project_files,
                progress_callback,
                stage_progress["assemble_project_files"],
                project_root,
                assembled_files_payload,
            )

            structure_report = self.pipeline.execute_stage(
                "validate_structure",
                self.validator.validate_structure,
                progress_callback,
                stage_progress["validate_structure"],
                project_root,
            )
            required_files_report = self.pipeline.execute_stage(
                "validate_required_files",
                self.validator.validate_required_files,
                progress_callback,
                stage_progress["validate_required_files"],
                project_root,
                manifest,
                generated_files,
            )
            non_empty_report = self.pipeline.execute_stage(
                "validate_non_empty_files",
                self.validator.validate_non_empty_files,
                progress_callback,
                stage_progress["validate_non_empty_files"],
                project_root,
            )
            manifest_consistency_report = self.pipeline.execute_stage(
                "validate_manifest_consistency",
                self.validator.validate_manifest_consistency,
                progress_callback,
                stage_progress["validate_manifest_consistency"],
                project_root,
                manifest,
                generated_files,
            )
            path_safety_report = self.pipeline.execute_stage(
                "validate_path_safety",
                self.validator.validate_path_safety,
                progress_callback,
                stage_progress["validate_path_safety"],
                generated_files,
            )
            syntax_report = self.pipeline.execute_stage(
                "optional_syntax_checks",
                self.validator.optional_syntax_checks,
                progress_callback,
                stage_progress["optional_syntax_checks"],
                project_root,
            )

            validation_report = self.validator.build_report(
                structure=structure_report,
                required_files=required_files_report,
                non_empty_files=non_empty_report,
                manifest_consistency=manifest_consistency_report,
                path_safety=path_safety_report,
                syntax=syntax_report,
            )
            repair_result = self.pipeline.execute_stage(
                "repair_if_needed",
                self.repair_if_needed,
                progress_callback,
                stage_progress["repair_if_needed"],
                project_root,
                assembled_files_payload,
                validation_report,
            )
            validation_report = self.pipeline.execute_stage(
                "revalidate_after_repair",
                self.revalidate_after_repair,
                progress_callback,
                stage_progress["revalidate_after_repair"],
                project_root,
                manifest,
                generated_files,
                repair_result,
                validation_report,
            )
            if not validation_report.get("valid", False):
                logger.warning(
                    "Validation found issues but delivering project anyway: structure=%s required_files=%s "
                    "non_empty=%s manifest=%s path_safety=%s syntax=%s",
                    validation_report.get("structure", {}).get("ok"),
                    validation_report.get("required_files", {}).get("ok"),
                    validation_report.get("non_empty_files", {}).get("ok"),
                    validation_report.get("manifest_consistency", {}).get("ok"),
                    validation_report.get("path_safety", {}).get("ok"),
                    validation_report.get("syntax", {}).get("ok"),
                )
                validation_report["partial"] = True

            package_result = self.pipeline.execute_stage(
                "package_to_zip",
                self.package_to_zip,
                progress_callback,
                stage_progress["package_to_zip"],
                project_root,
                zip_path,
            )
            project = self.pipeline.execute_stage(
                "persist_project_metadata",
                self.persist_project_metadata,
                progress_callback,
                stage_progress["persist_project_metadata"],
                {
                    "project_id": project_id,
                    "safe_project_name": safe_project_name,
                    "prompt": prompt,
                    "backend": backend,
                    "frontend": frontend,
                    "execution": execution,
                    "scaffold_strategy": scaffold_strategy,
                    "domain": domain,
                    "project_root": project_root,
                    "package_result": package_result,
                    "manifest": manifest,
                    "rag_context_summary": rag_context_summary,
                    "cache_info": {"hit": False, "fingerprint": request_fingerprint},
                    "generated_files": generated_files,
                    "validation_report": validation_report,
                    "artifact": artifact,
                },
            )
            cache_result = self.pipeline.execute_stage(
                "persist_generation_cache",
                self.persist_generation_cache,
                progress_callback,
                stage_progress["persist_generation_cache"],
                request_fingerprint,
                project,
                prompt,
                backend,
                frontend,
                expanded_features,
                domain,
                execution,
            )
            indexing_result = self.pipeline.execute_stage(
                "index_generated_project_into_rag",
                self.index_generated_project_into_rag,
                progress_callback,
                stage_progress["index_generated_project_into_rag"],
                project.project_path,
                domain,
                expanded_features,
            )

            result = {
                "project_id": str(project.id),
                "project_path": project.project_path,
                "zip_path": project.zip_path,
                "manifest": project.manifest,
                "generated_files": project.generated_files,
                "validation_report": project.validation_report,
                "cache_info": project.cache_info,
                "blueprint_used": project.blueprint_used,
                "rag_retrieval_summary": project.rag_summary,
                "execution_mode": execution["mode"],
                "mode_selected": execution["mode"],
                "selection_score": execution["score"],
                "selection_candidates": execution["candidates"],
                "web_discovery_summary": web_discovery_summary,
                "rag_indexing": indexing_result,
                "stage_timings": self.pipeline.stage_timings,
            }
            return self.pipeline.execute_stage(
                "finalize_job_status",
                self.finalize_job_status,
                progress_callback,
                stage_progress["finalize_job_status"],
                result,
                project_root=project_root,
                artifact=artifact,
                cache_result=cache_result,
                indexing_result=indexing_result,
            )
        except Exception as exc:
            GENERATION_COUNTER.labels(status="failed").inc()
            logger.exception("Generation pipeline failed")
            raise GenerationException(str(exc)) from exc

    def validate_request(self, backend: str, frontend: str, prompt: str, mode_preference: str) -> None:
        if backend not in SUPPORTED_BACKENDS:
            raise ValidationException(f"Unsupported backend: {backend}")
        if frontend not in SUPPORTED_FRONTENDS:
            raise ValidationException(f"Unsupported frontend: {frontend}")
        if not prompt.strip():
            raise ValidationException("Prompt cannot be empty")
        if mode_preference not in {"auto", "reuse", "adapt", "generate", "hybrid_scaffold"}:
            raise ValidationException(f"Unsupported mode preference: {mode_preference}")

    def compute_fingerprint(self, prompt: str, backend: str, frontend: str, features: list[str]) -> str:
        return self.fingerprint_service.compute(
            prompt=prompt,
            backend=backend,
            frontend=frontend,
            features=features,
            domain=DEFAULT_DOMAIN,
            blueprint="scaffold",
        )

    def exact_cache_lookup(self, fingerprint: str):
        return self.cache_service.lookup(fingerprint)

    def parse_prompt(self, prompt: str) -> dict:
        return self.prompt_parser.parse_prompt(prompt)

    def classify_domain(self, parsed_prompt: dict) -> str:
        return self.domain_classifier.classify(parsed_prompt)

    def select_blueprint(self, domain: str, _parsed_prompt: dict) -> dict:
        return {"domain": domain, "strategy": "compat_scaffold", "default_features": self.default_scaffold_features(domain)}

    def expand_features(self, parsed_prompt: dict, features: list[str], domain: str) -> list[str]:
        scaffold_profile = {"default_features": self.default_scaffold_features(domain)}
        return self.feature_expander.expand(parsed_prompt, features, scaffold_profile)

    def discover_existing_projects(self, domain: str) -> list[Project]:
        return self.existing_search.find_candidates(domain=domain)

    def score_similarity(self, prompt: str, features: list[str], candidates: list[Project]) -> list[dict]:
        return self.base_selector.score_candidates(prompt, features, candidates)

    def select_execution_mode(self, mode_preference: str, scored_candidates: list[dict]) -> dict:
        return self.base_selector.determine_mode(scored_candidates=scored_candidates, mode_preference=mode_preference)

    def resolve_scaffold_strategy(self, domain: str, execution: dict) -> dict:
        mode = execution["mode"]
        if mode == "reuse":
            strategy = "reuse_existing_project"
        elif mode == "adapt":
            strategy = "adapt_existing_project"
        elif mode == "hybrid_scaffold":
            strategy = "hybrid_scaffold"
        elif domain != DEFAULT_DOMAIN:
            strategy = "domain_scaffold"
        else:
            strategy = "clean_scaffold"

        return {
            "strategy": strategy,
            "domain": domain,
            "default_features": self.default_scaffold_features(domain),
            "selection_score": execution.get("score", 0.0),
        }

    @staticmethod
    def select_base_project(execution: dict) -> Optional[Project]:
        return execution.get("selected")

    def retrieve_rag_context(
        self,
        prompt: str,
        domain: str,
        expanded_features: list[str],
        selected_base: Optional[Project],
    ) -> list[dict]:
        query_parts = [prompt, domain, " ".join(expanded_features)]
        if selected_base:
            query_parts.append(selected_base.description or "")
        query = "\n".join(part for part in query_parts if part)

        started = time.perf_counter()
        try:
            return self.rag_retriever.search(
                query=query,
                top_k=self.settings.max_rag_results,
                min_similarity=self.settings.rag_min_similarity,
            )
        except Exception as exc:
            logger.warning("RAG retrieval failed, continuing without context: %s", exc)
            return []
        finally:
            RAG_HISTOGRAM.observe(time.perf_counter() - started)

    def decide_if_web_discovery_needed(
        self,
        prompt: str,
        domain: str,
        website_like: Optional[str],
        execution: dict,
        rag_context_summary: dict,
    ) -> dict:
        return self.discovery_decider.decide(
            prompt=prompt,
            domain=domain,
            website_like=website_like,
            strong_reusable_project=execution.get("mode") == "reuse",
            rag_confidence=rag_context_summary.get("top_score", 0.0),
            adaptation_score=execution.get("score", 0.0),
        )

    def build_discovery_queries(
        self,
        prompt: str,
        domain: str,
        website_like: Optional[str],
        expanded_features: list[str],
        discovery_decision: dict,
    ) -> list[str]:
        if not discovery_decision.get("should_run"):
            return []

        feature_slice = " ".join(expanded_features[:4])
        queries = [f"{prompt} {domain} {feature_slice}".strip()]
        queries.append(f"{domain.replace('_', ' ')} reference architecture {feature_slice}".strip())
        if website_like:
            queries.insert(0, f"{website_like} {domain} ui patterns")
        return [query for query in queries if query]

    def search_web_sources(self, discovery_queries: list[str]) -> list[dict]:
        return self.web_discovery.search_web_sources(discovery_queries)

    def filter_trusted_sources(self, raw_web_sources: list[dict]) -> list[dict]:
        return self.web_discovery.filter_trusted_sources(raw_web_sources)

    def rank_trusted_sources(self, discovery_queries: list[str], trusted_sources: list[dict]) -> list[dict]:
        return self.web_discovery.rank_trusted_sources(discovery_queries, trusted_sources)

    def fetch_shortlisted_sources(self, ranked_sources: list[dict], discovery_decision: dict) -> list[dict]:
        return self.web_discovery.fetch_shortlisted_sources(ranked_sources, discovery_decision)

    def extract_structured_knowledge(self, ranked_sources: list[dict], fetched_sources: list[dict]) -> dict:
        return self.web_discovery.extract_structured_knowledge(ranked_sources, fetched_sources)

    def persist_web_discovery_metadata(
        self,
        job_id: Optional[UUID],
        discovery_queries: list[str],
        ranked_sources: list[dict],
        extracted_knowledge: dict,
    ) -> dict:
        return self.web_discovery.persist_web_discovery_metadata(
            job_id=job_id,
            discovery_queries=discovery_queries,
            ranked_sources=ranked_sources,
            knowledge=extracted_knowledge,
        )

    def optionally_index_web_knowledge_into_rag(
        self,
        discovery_decision: dict,
        extracted_knowledge: dict,
        domain: str,
        expanded_features: list[str],
    ) -> dict:
        return self.web_discovery.optionally_index_web_knowledge_into_rag(
            discovery_decision=discovery_decision,
            knowledge=extracted_knowledge,
            module_type=domain,
            tags=expanded_features,
        )

    def summarize_web_discovery(
        self,
        discovery_decision: dict,
        discovery_queries: list[str],
        ranked_sources: list[dict],
        extracted_knowledge: dict,
        persisted_discovery: dict,
        rag_ingestion: dict,
    ) -> dict:
        return self.web_discovery.summarize_web_discovery(
            discovery_decision=discovery_decision,
            discovery_queries=discovery_queries,
            ranked_sources=ranked_sources,
            knowledge=extracted_knowledge,
            persisted_discovery=persisted_discovery,
            rag_ingestion=rag_ingestion,
        )

    def build_project_spec(
        self,
        parsed_prompt: dict,
        safe_project_name: str,
        backend: str,
        frontend: str,
        expanded_features: list[str],
        domain: str,
        execution: dict,
        scaffold_strategy: dict,
        selected_base: Optional[Project],
        web_discovery_summary: dict,
    ) -> dict:
        merged_features = sorted(set(expanded_features + web_discovery_summary.get("extracted_features", [])))
        project_spec = self.project_spec_builder.build_project_spec(
            parsed_prompt=parsed_prompt,
            project_name=safe_project_name,
            backend=backend,
            frontend=frontend,
            features=merged_features,
        )
        project_spec["domain"] = domain
        project_spec["execution_mode"] = execution["mode"]
        project_spec["scaffold_strategy"] = scaffold_strategy
        project_spec["web_discovery"] = {
            "features": web_discovery_summary.get("extracted_features", []),
            "entities": web_discovery_summary.get("extracted_entities", []),
            "suggested_architecture": web_discovery_summary.get("suggested_architecture", []),
        }
        if selected_base:
            project_spec["base_project"] = {
                "id": str(selected_base.id),
                "name": selected_base.name,
                "domain": selected_base.domain,
            }
        return project_spec

    def build_api_contract(self, project_spec: dict) -> dict:
        return self.api_contract_builder.build_api_contract(project_spec)

    def build_manifest(self, project_spec: dict, api_contract: dict) -> dict:
        manifest = self.manifest_builder.build_manifest(project_spec, api_contract)
        manifest["scaffold_strategy"] = project_spec.get("scaffold_strategy", {}).get("strategy")
        manifest["execution_mode"] = project_spec.get("execution_mode")
        return manifest

    def build_final_enriched_prompt(
        self,
        prompt: str,
        project_spec: dict,
        api_contract: dict,
        rag_context: list[dict],
        scaffold_strategy: dict,
        execution: dict,
        web_discovery_summary: dict,
        adaptation_context_summary: dict,
    ) -> dict:
        pre_final_prompt = self.prompt_enricher_service.enrich(
            original_prompt=prompt,
            project_spec=project_spec,
            api_contract=api_contract,
            rag_context=rag_context,
            fallback_context={
                "scaffold_strategy": scaffold_strategy,
                "selection_score": execution.get("score"),
                "selection_candidates": execution.get("candidates", []),
                "web_discovery": {
                    "used": web_discovery_summary.get("used", False),
                    "reasons": web_discovery_summary.get("reasons", []),
                },
            },
        )
        final_enriched_prompt = self.merge_engine.merge_contexts(
            base_enriched_prompt=pre_final_prompt,
            adaptation_context=adaptation_context_summary,
            web_discovery_summary=web_discovery_summary,
        )
        return {
            "pre_final_prompt": pre_final_prompt,
            "final_enriched_prompt": final_enriched_prompt,
        }

    def persist_prompt_artifacts(
        self,
        job_id: Optional[UUID],
        prompt: str,
        parsed_prompt: dict,
        expanded_features: list[str],
        execution_mode: str,
        rag_context_summary: dict,
        web_discovery_summary: dict,
        adaptation_context_summary: dict,
        ranked_sources: list[dict],
        pre_final_prompt: Optional[str],
        final_enriched_prompt: str,
    ):
        if not job_id:
            return None

        trusted_sources = [
            {
                "url": item.get("url"),
                "title": item.get("title"),
                "trust_score": item.get("trust_score"),
                "rank": item.get("rank"),
            }
            for item in ranked_sources[:10]
        ]

        return self.prompt_debugger.persist_prompt_artifact(
            job_id=job_id,
            raw_user_prompt=prompt,
            parsed_prompt=parsed_prompt,
            parsed_prompt_summary=self.build_parsed_prompt_summary(parsed_prompt),
            expanded_features=expanded_features,
            execution_mode=execution_mode,
            rag_summary={
                "retrieved_chunks": rag_context_summary.get("retrieved_chunks", 0),
                "top_score": rag_context_summary.get("top_score", 0.0),
                "sources": rag_context_summary.get("sources", []),
            },
            rag_context_summary=rag_context_summary,
            web_discovery_summary=web_discovery_summary,
            adaptation_context_summary=adaptation_context_summary,
            trusted_sources=trusted_sources,
            pre_final_prompt=pre_final_prompt,
            final_enriched_prompt=final_enriched_prompt,
            system_prompt=SYSTEM_PROMPT_ARCHITECT,
        )

    def create_project_skeleton(self, project_root: Path, project_id: UUID) -> dict:
        ensure_directory(project_root)
        return self.skeleton_builder.create(project_root, project_id)

    def generate_backend_code(self, project_spec: dict, api_contract: dict, rag_context: list[dict]) -> dict[str, str]:
        return self.spring_generator.generate(project_spec, api_contract, rag_context)

    def generate_frontend_code(self, project_spec: dict, api_contract: dict, rag_context: list[dict]) -> dict[str, str]:
        return self.angular_generator.generate(project_spec, api_contract, rag_context)

    def generate_docker_files(self, project_spec: dict, api_contract: dict, rag_context: list[dict]) -> dict[str, str]:
        return self.docker_generator.generate(project_spec, api_contract, rag_context)

    def generate_readme(self, project_spec: dict, api_contract: dict, manifest: dict) -> dict[str, str]:
        files = self.readme_generator.generate(project_spec, api_contract, [])
        files["manifest.json"] = json.dumps(manifest, indent=2)
        return files

    def assemble_project_files(self, project_root: Path, files: dict[str, str]) -> list[str]:
        return self.assembler.assemble_project_files(project_root, files)

    def repair_if_needed(self, project_root: Path, assembled_files_payload: dict[str, str], validation_report: dict) -> dict:
        return self.repair_engine.repair_if_needed(project_root, assembled_files_payload, validation_report)

    def revalidate_after_repair(
        self,
        project_root: Path,
        manifest: dict,
        generated_files: list[str],
        repair_result: dict,
        validation_report: dict,
    ) -> dict:
        if not repair_result.get("attempted"):
            return validation_report

        return self.validator.build_report(
            structure=self.validator.validate_structure(project_root),
            required_files=self.validator.validate_required_files(project_root, manifest, generated_files),
            non_empty_files=self.validator.validate_non_empty_files(project_root),
            manifest_consistency=self.validator.validate_manifest_consistency(project_root, manifest, generated_files),
            path_safety=self.validator.validate_path_safety(generated_files),
            syntax=self.validator.optional_syntax_checks(project_root),
        )

    def package_to_zip(self, project_root: Path, zip_path: Path) -> dict:
        return {"zip_path": self.packager.package_to_zip(project_root, zip_path)}

    def persist_project_metadata(self, record: dict) -> Project:
        project_root: Path = record["project_root"]
        project = Project(
            id=record["project_id"],
            name=record["safe_project_name"],
            description=record["prompt"],
            backend_stack=record["backend"],
            frontend_stack=record["frontend"],
            execution_mode=record["execution"]["mode"],
            domain=record["domain"],
            blueprint_used=record["scaffold_strategy"].get("strategy"),
            project_path=str(project_root),
            zip_path=record["package_result"]["zip_path"],
            manifest=record["manifest"],
            rag_summary=record["rag_context_summary"],
            cache_info=record["cache_info"],
            final_prompt_text_path=str(project_root / "_meta" / "final_enriched_prompt.txt"),
            final_prompt_json_path=str(project_root / "_meta" / "final_enriched_prompt.json"),
            generated_files=record["generated_files"],
            validation_report=record["validation_report"],
        )
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)

        artifact = record.get("artifact")
        if artifact:
            self.prompt_debugger.write_project_prompt_files(project_root, artifact, project.id)

        return project

    def persist_generation_cache(
        self,
        request_fingerprint: str,
        project: Project,
        prompt: str,
        backend: str,
        frontend: str,
        expanded_features: list[str],
        domain: str,
        execution: dict,
    ) -> dict:
        cache = self.cache_service.store(
            fingerprint=request_fingerprint,
            project=project,
            request_payload={
                "prompt": prompt,
                "backend": backend,
                "frontend": frontend,
                "features": expanded_features,
            },
            cache_metadata={
                "domain": domain,
                "execution_mode": execution["mode"],
                "selection_score": execution.get("score", 0.0),
            },
        )
        return {"stored": True, "cache_id": str(cache.id), "fingerprint": request_fingerprint}

    def index_generated_project_into_rag(self, project_path: str, domain: str, expanded_features: list[str]) -> dict:
        try:
            result = self.post_generation_indexer.index_generated_project(project_path, domain, expanded_features)
            return {"attempted": True, **result}
        except Exception as exc:
            logger.warning("Post-generation indexing failed: %s", exc)
            return {"attempted": True, "indexed_files": 0, "indexed_chunks": 0, "error": str(exc)}

    def finalize_job_status(
        self,
        result: dict,
        project_root: Optional[Path],
        artifact,
        cache_result: dict,
        indexing_result: dict,
    ) -> dict:
        self._validate_zip_exists(result)
        self._validate_required_artifacts(project_root)
        self._validate_prompt_artifacts(artifact)
        self._validate_stage_completion(cache_result, indexing_result)

        result["stage_timings"] = self.pipeline.stage_timings
        GENERATION_COUNTER.labels(status="completed").inc()
        return result

    @staticmethod
    def _validate_zip_exists(result: dict) -> None:
        zip_path = Path(result["zip_path"])
        if not zip_path.exists():
            raise ValidationException("ZIP artifact was not created")

    @staticmethod
    def _validate_required_artifacts(project_root: Optional[Path]) -> None:
        if not project_root:
            return
        for required_file in MANDATORY_OUTPUT_FILES:
            if not (project_root / required_file).exists():
                raise ValidationException(f"Missing critical artifact: {required_file}")

    @staticmethod
    def _validate_prompt_artifacts(artifact) -> None:
        if not artifact:
            return
        if not artifact.artifact_text_path or not Path(artifact.artifact_text_path).exists():
            raise ValidationException("Prompt text artifact missing")
        if not artifact.artifact_json_path or not Path(artifact.artifact_json_path).exists():
            raise ValidationException("Prompt JSON artifact missing")

    @staticmethod
    def _validate_stage_completion(cache_result: dict, indexing_result: dict) -> None:
        if not cache_result:
            raise ValidationException("Cache persistence stage did not return a result")
        if not indexing_result:
            raise ValidationException("RAG indexing stage did not return a result")

    def build_adaptation_context(
        self,
        execution_mode: str,
        selected_base: Optional[Project],
        prompt: str,
        expanded_features: list[str],
        website_like: Optional[str],
    ) -> dict:
        if execution_mode not in {"adapt", "hybrid_scaffold"} or not selected_base:
            return {}

        diff_summary = self.project_differ.diff(selected_base, prompt, expanded_features, website_like)
        return self.project_adapter.build_adaptation_context(selected_base, diff_summary)

    @staticmethod
    def build_parsed_prompt_summary(parsed_prompt: dict) -> dict:
        return {
            "summary": parsed_prompt.get("summary", ""),
            "token_count": len(parsed_prompt.get("tokens", [])),
            "entities": parsed_prompt.get("entities", []),
            "feature_hints": parsed_prompt.get("feature_hints", []),
        }

    @staticmethod
    def build_rag_context_summary(rag_context: list[dict]) -> dict:
        top_score = 0.0
        if rag_context:
            scores = [float(item.get("score") or 0.0) for item in rag_context]
            top_score = max(scores) if scores else 0.0

        return {
            "retrieved_chunks": len(rag_context),
            "top_score": round(top_score, 4),
            "sources": [item.get("metadata", {}) for item in rag_context[:5]],
        }

    def build_prompt_files_payload(
        self,
        job_id: Optional[UUID],
        project_id: UUID,
        prompt: str,
        parsed_prompt: dict,
        expanded_features: list[str],
        execution_mode: str,
        rag_context_summary: dict,
        web_discovery_summary: dict,
        adaptation_context_summary: dict,
        ranked_sources: list[dict],
        prompt_payload: dict,
    ) -> dict[str, str]:
        payload = {
            "job_id": str(job_id) if job_id else None,
            "project_id": str(project_id),
            "raw_user_prompt": prompt,
            "parsed_prompt": parsed_prompt,
            "parsed_prompt_summary": self.build_parsed_prompt_summary(parsed_prompt),
            "expanded_features": expanded_features,
            "execution_mode": execution_mode,
            "rag_summary": {
                "retrieved_chunks": rag_context_summary.get("retrieved_chunks", 0),
                "top_score": rag_context_summary.get("top_score", 0.0),
            },
            "rag_context_summary": rag_context_summary,
            "web_discovery_summary": web_discovery_summary,
            "adaptation_context_summary": adaptation_context_summary,
            "trusted_sources": [
                {
                    "url": item.get("url"),
                    "title": item.get("title"),
                    "trust_score": item.get("trust_score"),
                    "rank": item.get("rank"),
                }
                for item in ranked_sources[:10]
            ],
            "pre_final_prompt": prompt_payload.get("pre_final_prompt"),
            "final_enriched_prompt": prompt_payload["final_enriched_prompt"],
            "system_prompt": SYSTEM_PROMPT_ARCHITECT,
        }

        return {
            "_meta/final_enriched_prompt.txt": prompt_payload["final_enriched_prompt"],
            "_meta/final_enriched_prompt.json": json.dumps(payload, indent=2, ensure_ascii=False),
        }

    @staticmethod
    def default_scaffold_features(domain: str) -> list[str]:
        defaults = {
            "crm": ["dashboard", "reports", "authentication"],
            "hotel_management": ["booking", "dashboard", "reports"],
            "inventory_management": ["dashboard", "reports", "analytics"],
            "hospital_management": ["dashboard", "notifications", "reports"],
            "ecommerce": ["catalog", "orders", "payments"],
        }
        return defaults.get(domain, [])

    def build_reused_result(
        self,
        project: Project,
        request_fingerprint: str,
        execution_mode: str,
        cache_hit: bool,
        selection_score: Optional[float] = None,
        selection_candidates: Optional[list[dict]] = None,
    ) -> dict:
        result = {
            "project_id": str(project.id),
            "project_path": project.project_path,
            "zip_path": project.zip_path,
            "manifest": project.manifest,
            "generated_files": project.generated_files,
            "validation_report": project.validation_report,
            "cache_info": {"hit": cache_hit, "fingerprint": request_fingerprint},
            "blueprint_used": project.blueprint_used,
            "rag_retrieval_summary": project.rag_summary,
            "execution_mode": execution_mode,
            "mode_selected": execution_mode,
            "stage_timings": self.pipeline.stage_timings,
        }
        if selection_score is not None:
            result["selection_score"] = selection_score
        if selection_candidates is not None:
            result["selection_candidates"] = selection_candidates
        return result

    def _build_project_root(self, project_id: UUID, safe_project_name: str) -> Path:
        ensure_directory(self.settings.generated_projects_dir)
        return self.settings.generated_projects_dir / f"{safe_project_name}-{str(project_id)[:8]}"

    def _stage_progress_map(self) -> dict[str, int]:
        total = len(self.STAGES)
        return {
            stage: min(100, max(1, round(index * 100 / total)))
            for index, stage in enumerate(self.STAGES, start=1)
        }