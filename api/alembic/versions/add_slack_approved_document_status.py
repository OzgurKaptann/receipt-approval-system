from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "f1cb4455cf15"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Sprint-2 Step 1:
    Status for uploaded_documents is stored as VARCHAR(32), so Postgres does not
    need a type/ENUM alteration to allow SLACK_* values. This migration exists
    to record the schema version corresponding to the new application-level
    DocumentStatus values (SLACK_PENDING, SLACK_APPROVED, SLACK_REJECTED).
    """
    # No-op: database already accepts the new status strings.
    pass


def downgrade() -> None:
    # No-op: existing rows may already use the SLACK_* statuses.
    pass

