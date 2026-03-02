from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "customers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("crm_customer_id", sa.String(length=80), nullable=False),
        sa.Column("mt_account_id", sa.String(length=80), nullable=False),
        sa.Column("mt_currency", sa.String(length=3), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_unique_constraint("uq_customers_crm_customer_id", "customers", ["crm_customer_id"])
    op.create_unique_constraint("uq_customers_mt_account_id", "customers", ["mt_account_id"])

    op.create_table(
        "uploaded_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id"), nullable=False),

        sa.Column("receipt_amount_try", sa.Numeric(18, 2), nullable=False),

        sa.Column("original_file_name", sa.String(255), nullable=False),
        sa.Column("storage_file_name", sa.String(255), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("mime_type", sa.String(120), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        sa.Column("file_sha256", sa.String(64), nullable=False),

        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),

        sa.Column("public_key", sa.String(80), nullable=False),

        sa.Column("tg_chat_id", sa.String(40), nullable=True),
        sa.Column("tg_message_id", sa.String(40), nullable=True),
        sa.Column("tg_decided_by", sa.String(120), nullable=True),
        sa.Column("tg_decided_at", sa.DateTime(timezone=True), nullable=True),

        sa.Column("slack_channel_id", sa.String(40), nullable=True),
        sa.Column("slack_message_ts", sa.String(40), nullable=True),
        sa.Column("slack_decided_by", sa.String(120), nullable=True),
        sa.Column("slack_decided_at", sa.DateTime(timezone=True), nullable=True),

        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_unique_constraint("uq_uploaded_documents_file_sha256", "uploaded_documents", ["file_sha256"])
    op.create_unique_constraint("uq_uploaded_documents_public_key", "uploaded_documents", ["public_key"])

    op.create_table(
        "deposits",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("uploaded_documents.id"), nullable=False),

        sa.Column("mt_account_id", sa.String(80), nullable=False),

        sa.Column("src_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("src_currency", sa.String(3), nullable=False),

        sa.Column("fx_rate", sa.Numeric(18, 6), nullable=False),
        sa.Column("dst_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("dst_currency", sa.String(3), nullable=False),

        sa.Column("provider", sa.String(20), nullable=False),
        sa.Column("provider_ref", sa.String(120), nullable=True),

        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),

        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_unique_constraint("uq_deposits_document_id", "deposits", ["document_id"])

    op.create_table(
        "audit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("uploaded_documents.id"), nullable=True),

        sa.Column("event_type", sa.String(40), nullable=False),
        sa.Column("actor_type", sa.String(20), nullable=False),
        sa.Column("actor_id", sa.String(120), nullable=True),

        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_audit_events_document_id", "audit_events", ["document_id"], unique=False)


def downgrade():
    op.drop_index("ix_audit_events_document_id", table_name="audit_events")
    op.drop_table("audit_events")

    op.drop_constraint("uq_deposits_document_id", "deposits", type_="unique")
    op.drop_table("deposits")

    op.drop_constraint("uq_uploaded_documents_public_key", "uploaded_documents", type_="unique")
    op.drop_constraint("uq_uploaded_documents_file_sha256", "uploaded_documents", type_="unique")
    op.drop_table("uploaded_documents")

    op.drop_constraint("uq_customers_mt_account_id", "customers", type_="unique")
    op.drop_constraint("uq_customers_crm_customer_id", "customers", type_="unique")
    op.drop_table("customers")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")