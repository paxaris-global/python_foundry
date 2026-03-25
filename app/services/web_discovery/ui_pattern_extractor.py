class UIPatternExtractor:
    def extract(self, page_data: dict) -> list[str]:
        text = (page_data.get("text") or "").lower()
        headings = " ".join(page_data.get("headings", [])).lower()
        corpus = f"{text} {headings}"

        patterns = []
        for token, label in [
            ("dashboard", "dashboard_layout"),
            ("table", "data_table"),
            ("card", "summary_cards"),
            ("form", "form_workflow"),
            ("analytics", "analytics_widgets"),
            ("sidebar", "sidebar_navigation"),
            ("pricing", "pricing_section"),
        ]:
            if token in corpus:
                patterns.append(label)
        return sorted(set(patterns))
