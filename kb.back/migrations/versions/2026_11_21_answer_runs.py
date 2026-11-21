"""Add answer_runs and answer_feedback for AI Answers."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "answer_runs"
down_revision = "indexing_projection"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "answer_runs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("principal_id", sa.Uuid(), nullable=False),
        sa.Column("principal_type", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("stage", sa.String(32)),
        sa.Column("stage_sequence", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("question", sa.Text()),
        sa.Column("space_ids", postgresql.ARRAY(sa.Uuid())),
        sa.Column("actor_roles", postgresql.ARRAY(sa.String()), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("answer_status", sa.String(64)),
        sa.Column("response", postgresql.JSONB()),
        sa.Column("provider", sa.String(64)),
        sa.Column("model_id", sa.String(128)),
        sa.Column("prompt_version", sa.String(64)),
        sa.Column("retrieval_version", sa.String(64)),
        sa.Column("usage", postgresql.JSONB()),
        sa.Column("estimated_cost_usd", sa.Numeric(12, 6)),
        sa.Column("metrics", postgresql.JSONB()),
        sa.Column("results_count", sa.Integer()),
        sa.Column("sources_count", sa.Integer()),
        sa.Column("latency_ms", sa.Integer()),
        sa.Column("error_code", sa.String(64)),
        sa.Column("idempotency_key", sa.String(128)),
        sa.Column("lease_owner", sa.String(128)),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint(
            "organization_id",
            "principal_id",
            "idempotency_key",
            name="uq_answer_runs_idempotency",
        ),
    )
    op.create_index("ix_answer_runs_organization_id", "answer_runs", ["organization_id"])
    op.create_index("ix_answer_runs_status", "answer_runs", ["status"])
    op.create_index(
        "ix_answer_runs_org_principal_created",
        "answer_runs",
        ["organization_id", "principal_id", "created_at"],
    )
    op.create_index(
        "ix_answer_runs_lease_expires",
        "answer_runs",
        ["lease_expires_at"],
        postgresql_where=sa.text("status = 'running'"),
    )

    op.create_table(
        "answer_feedback",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("answer_id", sa.Uuid(), sa.ForeignKey("answer_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=False),
        sa.Column("helpful", sa.Boolean(), nullable=False),
        sa.Column("reason", sa.String(64)),
        sa.Column("comment", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("answer_id", "actor_id", name="uq_answer_feedback_actor"),
    )
    op.create_index("ix_answer_feedback_organization_id", "answer_feedback", ["organization_id"])


def downgrade() -> None:
    op.drop_table("answer_feedback")
    op.drop_index("ix_answer_runs_lease_expires", table_name="answer_runs")
    op.drop_index("ix_answer_runs_org_principal_created", table_name="answer_runs")
    op.drop_index("ix_answer_runs_status", table_name="answer_runs")
    op.drop_index("ix_answer_runs_organization_id", table_name="answer_runs")
    op.drop_table("answer_runs")
