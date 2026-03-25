from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class APIMessage(BaseModel):
    message: str


class TimestampedSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    created_at: datetime
    updated_at: datetime


class IDSchema(BaseModel):
    id: UUID
