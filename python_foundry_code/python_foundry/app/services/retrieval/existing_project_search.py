from typing import Optional

from sqlalchemy.orm import Session

from app.models.project import Project


class ExistingProjectSearch:
    def __init__(self, db: Session):
        self.db = db

    def find_candidates(self, domain: Optional[str], limit: int = 25) -> list[Project]:
        query = self.db.query(Project)
        if domain and domain != "general":
            query = query.filter(Project.domain == domain)

        return query.order_by(Project.updated_at.desc()).limit(limit).all()
