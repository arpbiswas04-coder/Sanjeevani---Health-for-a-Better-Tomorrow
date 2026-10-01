"""Align existing warehouse active flags with their authoritative facilities."""
from alembic import op

revision='c83d9e124a35'
down_revision='b72c8d013f24'
branch_labels=None
depends_on=None


def upgrade():
    op.execute('UPDATE warehouses SET active=(SELECT active FROM facilities WHERE facilities.id=warehouses.facility_id)')


def downgrade():
    # Deliberately preserve corrected operational state; old inconsistencies
    # cannot be reconstructed and must not be reintroduced during a downgrade.
    return
