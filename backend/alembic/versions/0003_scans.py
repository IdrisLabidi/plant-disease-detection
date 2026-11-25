"""add scan history"""

import sqlalchemy as sa

from alembic import op

revision = "0003_scans"
down_revision = "0002_oauth_identities"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scans",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("client_id", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(length=16), nullable=False),
        sa.Column("model_name", sa.String(length=64), nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=False),
        sa.Column("top_class", sa.String(length=255), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("top3", sa.JSON(), nullable=False),
        sa.Column("unsure", sa.Boolean(), nullable=False),
        sa.Column("lesion_area_frac", sa.Float(), nullable=True),
        sa.Column("image_path", sa.String(length=1000), nullable=True),
        sa.Column("mask_path", sa.String(length=1000), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "client_id", name="uq_scans_user_client"),
    )
    op.create_index("ix_scans_user_id", "scans", ["user_id"], unique=False)
    op.create_index("ix_scans_user_created", "scans", ["user_id", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_scans_user_created", table_name="scans")
    op.drop_index("ix_scans_user_id", table_name="scans")
    op.drop_table("scans")
