class APIContractBuilder:
    def build_api_contract(self, project_spec: dict) -> dict:
        base = "/api/v1"
        entity = "customers"
        return {
            "openapi": "3.0.3",
            "info": {
                "title": f"{project_spec['project_name']} API",
                "version": "1.0.0",
            },
            "paths": {
                f"{base}/{entity}": {
                    "get": {"summary": "List customers"},
                    "post": {"summary": "Create customer"},
                },
                f"{base}/{entity}/{{id}}": {
                    "get": {"summary": "Get customer"},
                    "put": {"summary": "Update customer"},
                    "delete": {"summary": "Delete customer"},
                },
            },
        }
