"""add web discovery and prompt artifacts

Revision ID: 0002_web_discovery_prompt
Revises: 0001_initial
Create Date: 2026-03-20
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0002_web_discovery_prompt"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

JSON_EMPTY_OBJECT = sa.text("'{}'::jsonb")
JSON_EMPTY_ARRAY = sa.text("'[]'::jsonb")
NOW = sa.text("now()")


def upgrade() -> None:
    op.add_column("jobs", sa.Column("website_like", sa.String(length=120), nullable=True))
    op.add_column("jobs", sa.Column("mode_preference", sa.String(length=30), nullable=False, server_default="auto"))
    op.add_column("jobs", sa.Column("mode_selected", sa.String(length=30), nullable=True))

    op.add_column("projects", sa.Column("execution_mode", sa.String(length=30), nullable=False, server_default="generate"))
    op.add_column("projects", sa.Column("final_prompt_text_path", sa.Text(), nullable=True))
    op.add_column("projects", sa.Column("final_prompt_json_path", sa.Text(), nullable=True))

    op.create_table(
        "prompt_artifacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("raw_user_prompt", sa.Text(), nullable=False),
        sa.Column("parsed_prompt", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=JSON_EMPTY_OBJECT),
        sa.Column("expanded_features", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=JSON_EMPTY_ARRAY),
        sa.Column("execution_mode", sa.String(length=30), nullable=False, server_default="generate"),
        sa.Column("rag_summary", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=JSON_EMPTY_OBJECT),
        sa.Column(
            "web_discovery_summary",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=JSON_EMPTY_OBJECT,
        ),
        sa.Column("trusted_sources", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=JSON_EMPTY_ARRAY),
        sa.Column("system_prompt", sa.Text(), nullable=True),
        sa.Column("final_enriched_prompt", sa.Text(), nullable=False),
        sa.Column("artifact_text_path", sa.Text(), nullable=True),
        sa.Column("artifact_json_path", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
    )
    op.create_index("ix_prompt_artifacts_job_id", "prompt_artifacts", ["job_id"])

    op.create_table(
        "web_discovery_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id"), nullable=True),
        sa.Column("query", sa.String(length=500), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="completed"),
        sa.Column("discovered_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("summary", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=JSON_EMPTY_OBJECT),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
    )
    op.create_index("ix_web_discovery_runs_job_id", "web_discovery_runs", ["job_id"])

    op.create_table(
        "web_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "discovery_run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("web_discovery_runs.id"),
            nullable=False,
        ),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=True),
        sa.Column("source_type", sa.String(length=50), nullable=False, server_default="web"),
        sa.Column("trust_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=JSON_EMPTY_OBJECT),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
    )
    op.create_index("ix_web_sources_discovery_run_id", "web_sources", ["discovery_run_id"])


def downgrade() -> None:
    op.drop_index("ix_web_sources_discovery_run_id", table_name="web_sources")
    op.drop_table("web_sources")

    op.drop_index("ix_web_discovery_runs_job_id", table_name="web_discovery_runs")
    op.drop_table("web_discovery_runs")

    op.drop_index("ix_prompt_artifacts_job_id", table_name="prompt_artifacts")
    op.drop_table("prompt_artifacts")

    op.drop_column("projects", "final_prompt_json_path")
    op.drop_column("projects", "final_prompt_text_path")
    op.drop_column("projects", "execution_mode")

    op.drop_column("jobs", "mode_selected")
    op.drop_column("jobs", "mode_preference")
    op.drop_column("jobs", "website_like")
