class APIContractBuilder:
    def build_api_contract(self, project_spec: dict) -> dict:
        base = "/api/v1"
        domain = str(project_spec.get("domain", "")).lower()
        paths = {
            f"{base}/customers": {
                "get": {"summary": "List customers"},
                "post": {"summary": "Create customer"},
            },
            f"{base}/customers/{{id}}": {
                "get": {"summary": "Get customer"},
                "put": {"summary": "Update customer"},
                "delete": {"summary": "Delete customer"},
            },
        }
        if domain in {"ecommerce", "retail"}:
            paths.update(
                {
                    f"{base}/products": {
                        "get": {"summary": "List products"},
                        "post": {"summary": "Create product"},
                    },
                    f"{base}/products/{{id}}": {
                        "get": {"summary": "Get product"},
                        "put": {"summary": "Update product"},
                        "delete": {"summary": "Delete product"},
                    },
                }
            )
        return {
            "openapi": "3.0.3",
            "info": {
                "title": f"{project_spec['project_name']} API",
                "version": "1.0.0",
            },
            "paths": paths,
        }
