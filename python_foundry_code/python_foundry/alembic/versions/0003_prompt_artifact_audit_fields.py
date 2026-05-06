"""add richer prompt artifact audit fields

Revision ID: 0003_prompt_artifact_audit
Revises: 0002_web_discovery_prompt
Create Date: 2026-03-20
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "0003_prompt_artifact_audit"
down_revision = "0002_web_discovery_prompt"
branch_labels = None
depends_on = None

JSON_EMPTY_OBJECT = sa.text("'{}'::jsonb")


def upgrade() -> None:
    op.add_column(
        "prompt_artifacts",
        sa.Column(
            "parsed_prompt_summary",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=JSON_EMPTY_OBJECT,
        ),
    )
    op.add_column(
        "prompt_artifacts",
        sa.Column(
            "rag_context_summary",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=JSON_EMPTY_OBJECT,
        ),
    )
    op.add_column(
        "prompt_artifacts",
        sa.Column(
            "adaptation_context_summary",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=JSON_EMPTY_OBJECT,
        ),
    )
    op.add_column("prompt_artifacts", sa.Column("pre_final_prompt", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("prompt_artifacts", "pre_final_prompt")
    op.drop_column("prompt_artifacts", "adaptation_context_summary")
    op.drop_column("prompt_artifacts", "rag_context_summary")
    op.drop_column("prompt_artifacts", "parsed_prompt_summary")
