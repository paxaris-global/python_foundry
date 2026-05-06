class DomainClassifier:
    KEYWORDS = {
        "hotel_management": ["hotel", "booking", "room", "check-in", "check out", "hospitality"],
        "ecommerce": ["e-commerce", "ecommerce", "catalog", "cart", "checkout", "order", "product"],
        "crm": ["crm", "lead", "customer", "sales pipeline", "account management"],
        "lms": ["lms", "course", "student", "teacher", "learning"],
        "inventory_management": ["inventory", "stock", "warehouse", "supply"],
        "hospital_management": ["hospital", "patient", "doctor", "clinic", "appointment"],
        "payroll_system": ["payroll", "salary", "employee", "tax"],
        "blog_cms": ["blog", "cms", "content", "post", "editor"],
    }

    def classify(self, parsed_prompt: dict) -> str:
        text = parsed_prompt.get("summary", "").lower()
        for domain, keywords in self.KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                return domain
        return "general"
