import json

from app.utils.hashing import sha256_text
from app.utils.sanitizers import sanitize_feature_list, sanitize_text


class FingerprintService:
    def compute(
        self,
        prompt: str,
        backend: str,
        frontend: str,
        features: list[str],
        domain: str = "general",
        blueprint: str = "default",
        template_version: str = "v1",
    ) -> str:
        payload = {
            "prompt": sanitize_text(prompt.lower()),
            "backend": backend.lower(),
            "frontend": frontend.lower(),
            "features": sanitize_feature_list(features),
            "domain": domain.lower(),
            "blueprint": blueprint.lower(),
            "template_version": sanitize_text(template_version.lower()),
        }
        return sha256_text(json.dumps(payload, sort_keys=True, ensure_ascii=True))
