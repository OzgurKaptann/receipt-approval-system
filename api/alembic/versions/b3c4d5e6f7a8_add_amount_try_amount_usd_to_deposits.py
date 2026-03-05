from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b3c4d5e6f7a8"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("deposits", sa.Column("amount_try", sa.Numeric(18, 2), nullable=True))
    op.add_column("deposits", sa.Column("amount_usd", sa.Numeric(18, 2), nullable=True))


def downgrade() -> None:
    op.drop_column("deposits", "amount_usd")
    op.drop_column("deposits", "amount_try")

