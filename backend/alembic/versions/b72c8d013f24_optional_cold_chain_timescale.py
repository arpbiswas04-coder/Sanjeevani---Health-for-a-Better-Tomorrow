"""Cold-chain series projection; explicitly opt in to TimescaleDB on PostgreSQL.

Set ENABLE_TIMESCALEDB=1 BEFORE upgrading this revision. Requires TimescaleDB
2.13+ installed/preloaded on the server. Never drops operational observations.
"""
import os
from alembic import op
import sqlalchemy as sa

revision='b72c8d013f24'
down_revision='a41b7c902e13'
branch_labels=None
depends_on=None


def upgrade():
    flag=os.environ.get('ENABLE_TIMESCALEDB','0')
    if flag not in ('0','1'):
        raise RuntimeError('ENABLE_TIMESCALEDB must be 0 or 1')
    pg=op.get_bind().dialect.name=='postgresql'
    op.create_table('cold_chain_samples',
        sa.Column('id',sa.Uuid(),primary_key=True),
        sa.Column('observed_at',sa.DateTime(timezone=True),primary_key=True),
        sa.Column('facility_id',sa.Uuid(),nullable=False),
        sa.Column('temperature',sa.Double(),nullable=False),
        sa.Column('minimum',sa.Double(),nullable=False),
        sa.Column('maximum',sa.Double(),nullable=False),
        sa.Column('excursion',sa.Boolean(),nullable=False),
        sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),
        sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False))
    op.create_index('ix_cold_chain_samples_facility_time','cold_chain_samples',['facility_id','observed_at'])
    if pg:
        # Deployment must pause ingestion; lock bounds the backfill consistently.
        op.execute("SET LOCAL lock_timeout = '10s'")
        op.execute('LOCK TABLE temperature_observations IN SHARE ROW EXCLUSIVE MODE')
    if pg and flag=='1':
        op.execute('CREATE EXTENSION IF NOT EXISTS timescaledb')
        op.execute("SELECT create_hypertable('cold_chain_samples',by_range('observed_at',INTERVAL '7 days'),create_default_indexes=>FALSE)")
    fields='id,observed_at,facility_id,temperature,minimum,maximum,excursion,created_at,updated_at'
    op.execute(sa.text(f'INSERT INTO cold_chain_samples ({fields}) SELECT {fields} FROM temperature_observations'))


def downgrade():
    # Only the rebuildable projection is dropped; source observations remain.
    op.drop_table('cold_chain_samples')
