from pydantic import BaseModel, Field


class ManifestSchema(BaseModel):
    project_name: str
    backend: dict
    frontend: dict
    features: list[str] = Field(default_factory=list)
    mandatory_files: list[str] = Field(default_factory=list)
