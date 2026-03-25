class ComponentExtractor:
    KEYWORDS = {
        "table": "DataTable",
        "chart": "AnalyticsChart",
        "card": "SummaryCard",
        "modal": "ActionModal",
        "form": "EntityForm",
        "sidebar": "SidebarNav",
        "navbar": "TopNav",
    }

    def extract(self, page_data: dict) -> list[str]:
        text = (page_data.get("text") or "").lower()
        components = [name for key, name in self.KEYWORDS.items() if key in text]
        return sorted(set(components))
