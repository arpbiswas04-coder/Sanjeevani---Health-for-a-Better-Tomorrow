"""Seed capabilities, preserve bootstrap administrator access, enforce ledger invariants.

Revision ID: 61a1f12dca10
Revises: 0d743597d6d7
"""
from datetime import datetime, timezone
from uuid import uuid4
from alembic import op
import sqlalchemy as sa

revision='61a1f12dca10'
down_revision='0d743597d6d7'
branch_labels=None
depends_on=None

CAPABILITIES=('inventory.read','inventory.write','inventory.transfer','inventory.recall','facility.manage',
    'procurement.read','procurement.write','procurement.approve','workforce.read','workforce.write','beds.read','beds.write',
    'equipment.read','equipment.write','alerts.read','alerts.manage','reports.read','reports.export','integration.read',
    'integration.write','admin.users','admin.config','emergency.activate','federation.manage','audit.read','sync.write')


def upgrade():
    with op.batch_alter_table('medicine_inventory') as batch:
        batch.create_check_constraint('ck_inventory_reserved','reserved >= 0 AND reserved <= quantity')
    with op.batch_alter_table('users') as batch:
        batch.create_check_constraint('ck_user_scope',"scope_mode IN ('restricted','global')")
    # Static INSERT...SELECT is portable and supports PostgreSQL offline SQL output.
    # Fixed UUID values are generated here only for new catalogue entries.
    permissions=sa.table('permissions',sa.column('id',sa.Uuid()),sa.column('name',sa.String()),
        sa.column('created_at',sa.DateTime(timezone=True)),sa.column('updated_at',sa.DateTime(timezone=True)))
    for name in CAPABILITIES:
        now=datetime.now(timezone.utc)
        values=sa.select(sa.literal(uuid4(),type_=sa.Uuid()),sa.literal(name),sa.literal(now),sa.literal(now)).where(
            ~sa.exists(sa.select(permissions.c.id).where(permissions.c.name==name)))
        op.execute(permissions.insert().from_select(['id','name','created_at','updated_at'],values))
    op.execute("INSERT INTO role_permissions (role_id,permission_id) SELECT r.id,p.id FROM roles r CROSS JOIN permissions p WHERE r.name='administrator' AND NOT EXISTS (SELECT 1 FROM role_permissions rp WHERE rp.role_id=r.id AND rp.permission_id=p.id)")
    op.execute("UPDATE users SET scope_mode='global' WHERE id IN (SELECT ur.user_id FROM user_roles ur JOIN roles r ON r.id=ur.role_id WHERE r.name='administrator')")
    if op.get_bind().dialect.name=='postgresql':
        op.execute('CREATE EXTENSION IF NOT EXISTS postgis')
        op.execute('CREATE INDEX ix_facilities_geography ON facilities USING gist ((ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography))')
        op.execute("""CREATE FUNCTION prevent_operational_record_changes() RETURNS trigger LANGUAGE plpgsql AS $$
            BEGIN RAISE EXCEPTION 'Operational ledger records are immutable'; END; $$""")
        for table in ('stock_transactions','audit_logs'):
            op.execute(f'CREATE TRIGGER immutable_{table} BEFORE UPDATE OR DELETE ON {table} FOR EACH ROW EXECUTE FUNCTION prevent_operational_record_changes()')


def downgrade():
    # Capability data and expanded administrator access are deliberately retained.
    if op.get_bind().dialect.name=='postgresql':
        for table in ('stock_transactions','audit_logs'):
            op.execute(f'DROP TRIGGER IF EXISTS immutable_{table} ON {table}')
        op.execute('DROP FUNCTION IF EXISTS prevent_operational_record_changes()')
        op.execute('DROP INDEX IF EXISTS ix_facilities_geography')
    with op.batch_alter_table('users') as batch:
        batch.drop_constraint('ck_user_scope',type_='check')
    with op.batch_alter_table('medicine_inventory') as batch:
        batch.drop_constraint('ck_inventory_reserved',type_='check')
