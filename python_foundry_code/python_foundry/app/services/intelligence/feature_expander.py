from app.utils.sanitizers import sanitize_feature_list


class FeatureExpander:
    def expand(self, parsed_prompt: dict, features: list[str], blueprint: dict) -> list[str]:
        extracted = parsed_prompt.get("feature_hints", [])
        blueprint_features = blueprint.get("default_features", [])
        return sanitize_feature_list(features + extracted + blueprint_features)
