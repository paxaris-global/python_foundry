from typing import Optional

from app.utils.json_utils import to_pretty_json


class MergeEngine:
    def merge_contexts(
        self,
        base_enriched_prompt: str,
        adaptation_context: Optional[dict],
        web_discovery_summary: Optional[dict],
    ) -> str:
        payload = [base_enriched_prompt]

        if adaptation_context:
            payload.append("AdaptationContext:\n" + to_pretty_json(adaptation_context))

        if web_discovery_summary:
            payload.append("WebDiscoverySummary:\n" + to_pretty_json(web_discovery_summary))

        return "\n\n".join(payload)
