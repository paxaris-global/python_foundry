import re


class EntityExtractor:
    COMMON_ENTITIES = [
        "user",
        "customer",
        "booking",
        "room",
        "product",
        "order",
        "invoice",
        "payment",
        "employee",
        "patient",
        "course",
    ]

    def extract(self, page_data: dict) -> list[str]:
        text = (page_data.get("text") or "").lower()
        found = [entity for entity in self.COMMON_ENTITIES if re.search(rf"\b{re.escape(entity)}\b", text)]
        return sorted(set(found))
