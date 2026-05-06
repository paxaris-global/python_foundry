class RouteExtractor:
    def extract(self, page_data: dict) -> list[str]:
        routes = []

        for link in page_data.get("nav_links", []):
            href = link.get("href", "").strip()
            if href.startswith("/") and len(href) < 80:
                routes.append(href)

        headings = [h.lower() for h in page_data.get("headings", [])]
        for heading in headings:
            slug = heading.replace(" ", "-")
            if len(slug) < 60 and slug:
                routes.append(f"/{slug}")

        return sorted(set(routes))[:80]
