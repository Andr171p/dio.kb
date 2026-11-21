"""Add knowledge gaps and gap signals tables."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "knowledge_gaps"
down_revision = "answer_runs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "gap_signals",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(64), nullable=False),
        sa.Column("source_type", sa.String(64), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("answer_id", sa.Uuid()),
        sa.Column("article_ids", postgresql.ARRAY(sa.Uuid())),
        sa.Column("topic_hint", sa.String(255)),
        sa.Column("space_id", sa.Uuid()),
        sa.Column("metadata", postgresql.JSONB()),
        sa.Column("processed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint(
            "organization_id",
            "source_type",
            "source_id",
            "kind",
            name="uq_gap_signals_source",
        ),
    )
    op.create_index("ix_gap_signals_organization_id", "gap_signals", ["organization_id"])
    op.create_index(
        "ix_gap_signals_org_occurred",
        "gap_signals",
        ["organization_id", "occurred_at"],
    )
    op.create_index(
        "ix_gap_signals_unprocessed",
        "gap_signals",
        ["organization_id", "processed_at"],
        postgresql_where=sa.text("processed_at IS NULL"),
    )

    op.create_table(
        "knowledge_gaps",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("space_id", sa.Uuid()),
        sa.Column("grouping_key", sa.String(128), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("kind", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("owner_id", sa.Uuid()),
        sa.Column("related_article_id", sa.Uuid()),
        sa.Column("resolution_note", sa.Text()),
        sa.Column("rationale", sa.Text()),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("organization_id", "grouping_key", name="uq_knowledge_gaps_grouping"),
    )
    op.create_index("ix_knowledge_gaps_organization_id", "knowledge_gaps", ["organization_id"])
    op.create_index("ix_knowledge_gaps_status", "knowledge_gaps", ["status"])
    op.create_index(
        "ix_knowledge_gaps_org_status_space",
        "knowledge_gaps",
        ["organization_id", "status", "space_id"],
    )
    op.create_index(
        "ix_knowledge_gaps_org_owner_status",
        "knowledge_gaps",
        ["organization_id", "owner_id", "status"],
    )

    op.create_table(
        "knowledge_gap_signals",
        sa.Column("gap_id", sa.Uuid(), sa.ForeignKey("knowledge_gaps.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("signal_id", sa.Uuid(), sa.ForeignKey("gap_signals.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("gap_id", "signal_id", name="uq_knowledge_gap_signals"),
    )
    op.create_index("ix_knowledge_gap_signals_organization_id", "knowledge_gap_signals", ["organization_id"])


def downgrade() -> None:
    op.drop_table("knowledge_gap_signals")
    op.drop_index("ix_knowledge_gaps_org_owner_status", table_name="knowledge_gaps")
    op.drop_index("ix_knowledge_gaps_org_status_space", table_name="knowledge_gaps")
    op.drop_index("ix_knowledge_gaps_status", table_name="knowledge_gaps")
    op.drop_index("ix_knowledge_gaps_organization_id", table_name="knowledge_gaps")
    op.drop_table("knowledge_gaps")
    op.drop_index("ix_gap_signals_unprocessed", table_name="gap_signals")
    op.drop_index("ix_gap_signals_org_occurred", table_name="gap_signals")
    op.drop_index("ix_gap_signals_organization_id", table_name="gap_signals")
    op.drop_table("gap_signals")
