"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-03-20
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

JSON_EMPTY_OBJECT = sa.text("'{}'::jsonb")
JSON_EMPTY_ARRAY = sa.text("'[]'::jsonb")
NOW = sa.text("now()")


def upgrade() -> None:
    job_status = sa.Enum("pending", "running", "completed", "failed", name="jobstatus")
    job_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("backend_stack", sa.String(length=50), nullable=False),
        sa.Column("frontend_stack", sa.String(length=50), nullable=False),
        sa.Column("domain", sa.String(length=100), nullable=False, server_default="general"),
        sa.Column("blueprint_used", sa.String(length=120), nullable=True),
        sa.Column("project_path", sa.Text(), nullable=False),
        sa.Column("zip_path", sa.Text(), nullable=False),
        sa.Column("manifest", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=JSON_EMPTY_OBJECT),
        sa.Column("rag_summary", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=JSON_EMPTY_OBJECT),
        sa.Column("cache_info", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=JSON_EMPTY_OBJECT),
        sa.Column("generated_files", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=JSON_EMPTY_ARRAY),
        sa.Column("validation_report", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=JSON_EMPTY_OBJECT),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
    )

    op.create_table(
        "rag_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("source_path", sa.Text(), nullable=False),
        sa.Column("language", sa.String(length=30), nullable=False),
        sa.Column("module_type", sa.String(length=100), nullable=True),
        sa.Column("source_type", sa.String(length=50), nullable=False, server_default="repo"),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=JSON_EMPTY_ARRAY),
        sa.Column("content_hash", sa.String(length=128), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=JSON_EMPTY_OBJECT),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
    )

    op.create_table(
        "jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_name", sa.String(length=150), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("backend", sa.String(length=50), nullable=False),
        sa.Column("frontend", sa.String(length=50), nullable=False),
        sa.Column("features", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=JSON_EMPTY_ARRAY),
        sa.Column("fingerprint", sa.String(length=128), nullable=False),
        sa.Column("status", job_status, nullable=False, server_default="pending"),
        sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("current_stage", sa.String(length=120), nullable=False, server_default="pending"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("trace_id", sa.String(length=64), nullable=True),
        sa.Column("cache_hit", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("stage_timings", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=JSON_EMPTY_OBJECT),
        sa.Column("result_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=JSON_EMPTY_OBJECT),
        sa.Column("celery_task_id", sa.String(length=255), nullable=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
    )
    op.create_index("ix_jobs_fingerprint", "jobs", ["fingerprint"])
    op.create_index("ix_jobs_trace_id", "jobs", ["trace_id"])

    op.create_table(
        "generation_cache",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("fingerprint", sa.String(length=128), nullable=False),
        sa.Column("request_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=JSON_EMPTY_OBJECT),
        sa.Column("cache_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=JSON_EMPTY_OBJECT),
        sa.Column("hit_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.UniqueConstraint("fingerprint", name="uq_generation_cache_fingerprint"),
    )
    op.create_index("ix_generation_cache_fingerprint", "generation_cache", ["fingerprint"])


def downgrade() -> None:
    op.drop_index("ix_generation_cache_fingerprint", table_name="generation_cache")
    op.drop_table("generation_cache")
    op.drop_index("ix_jobs_trace_id", table_name="jobs")
    op.drop_index("ix_jobs_fingerprint", table_name="jobs")
    op.drop_table("jobs")
    op.drop_table("rag_documents")
    op.drop_table("projects")

    job_status = sa.Enum("pending", "running", "completed", "failed", name="jobstatus")
    job_status.drop(op.get_bind(), checkfirst=True)
