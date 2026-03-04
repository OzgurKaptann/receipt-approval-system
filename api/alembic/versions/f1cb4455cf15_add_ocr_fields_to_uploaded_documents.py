from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "f1cb4455cf15"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "uploaded_documents",
        sa.Column("sender_name", sa.String(length=255), nullable=True),
    )

    op.add_column(
        "uploaded_documents",
        sa.Column("transfer_date", sa.DateTime(timezone=True), nullable=True),
    )

    op.alter_column(
        "uploaded_documents",
        "receipt_amount_try",
        existing_type=sa.Numeric(precision=18, scale=2),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "uploaded_documents",
        "receipt_amount_try",
        existing_type=sa.Numeric(precision=18, scale=2),
        nullable=False,
    )

    op.drop_column("uploaded_documents", "transfer_date")
    op.drop_column("uploaded_documents", "sender_name")