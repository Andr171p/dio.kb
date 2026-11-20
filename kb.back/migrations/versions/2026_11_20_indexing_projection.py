"""Replace legacy index state and caches with versioned indexing storage."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "indexing_projection"
down_revision = "bdff3c8e6874"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("article_index_states")
    op.drop_table("image_texts")
    op.create_table(
        "image_analysis",
        sa.Column("media_id", sa.Uuid(), primary_key=True),
        sa.Column("version", sa.String(255), primary_key=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "embeddings",
        sa.Column("content_hash", sa.String(64), primary_key=True),
        sa.Column("version", sa.String(255), primary_key=True),
        sa.Column("vector", postgresql.ARRAY(sa.Float()), nullable=False),
    )
    op.create_table(
        "index_checkpoints",
        sa.Column("article_id", sa.Uuid(), sa.ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("generation", sa.String(255), primary_key=True),
        sa.Column("revision_id", sa.Uuid(), nullable=False),
        sa.Column("space_id", sa.Uuid(), nullable=False),
        sa.Column("indexed_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("index_checkpoints")
    op.drop_table("embeddings")
    op.drop_table("image_analysis")
    op.create_table(
        "image_texts",
        sa.Column("media_id", sa.Uuid(), primary_key=True),
        sa.Column("version", sa.String(255), primary_key=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "article_index_states",
        sa.Column("article_id", sa.Uuid(), sa.ForeignKey("articles.id"), primary_key=True),
        sa.Column("revision_id", sa.Uuid()),
        sa.Column("index_name", sa.String(255), nullable=False),
        sa.Column("chunk_count", sa.Integer(), nullable=False),
        sa.Column("failed_media_ids", postgresql.ARRAY(sa.Uuid()), nullable=False, server_default="{}"),
        sa.Column("indexed_at", sa.DateTime(timezone=True), nullable=False),
    )
