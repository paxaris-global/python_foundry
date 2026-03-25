from app.db import base  # noqa: F401
from app.db.session import engine
from app.models.base import Base


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
