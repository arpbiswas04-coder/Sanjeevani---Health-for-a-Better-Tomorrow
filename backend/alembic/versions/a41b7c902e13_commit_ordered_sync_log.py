"""Commit-ordered aggregate sync with backfill of existing records."""
from alembic import op
import sqlalchemy as sa

revision='a41b7c902e13'
down_revision='f92e36664324'
branch_labels=None
depends_on=None


def record_columns():
    return [sa.Column('id',sa.Uuid(),primary_key=True),
            sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),
            sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False)]


def upgrade():
    op.create_table('sync_clock',sa.Column('sequence',sa.BigInteger(),nullable=False),*record_columns())
    op.create_table('sync_changes',sa.Column('sequence',sa.BigInteger(),nullable=False),
        sa.Column('kind',sa.String(30),nullable=False),
        sa.Column('facility_id',sa.Uuid(),sa.ForeignKey('facilities.id'),nullable=False),
        sa.Column('entity_id',sa.Uuid(),nullable=False),sa.Column('payload',sa.JSON(),nullable=False),*record_columns())
    op.create_index('ix_sync_changes_sequence','sync_changes',['sequence'],unique=True)
    op.create_index('ix_sync_changes_facility_id','sync_changes',['facility_id'])
    pg=op.get_bind().dialect.name=='postgresql'
    clock='00000000-0000-0000-0000-000000000001' if pg else '00000000000000000000000000000001'
    op.execute(sa.text(f"INSERT INTO sync_clock (id,sequence,created_at,updated_at) VALUES ('{clock}',0,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)"))
    # Pure SQL works both online and in reviewed offline migration output.
    for table,kind in [('patient_footfall_aggregates','footfall'),('disease_counts','disease-counts')]:
        fields=['id','facility_id','day','category','count','version','source_device','created_at','updated_at']
        values=[]
        for field in fields:
            value=field
            if not pg and field in ('id','facility_id'):
                value=f"substr({field},1,8)||'-'||substr({field},9,4)||'-'||substr({field},13,4)||'-'||substr({field},17,4)||'-'||substr({field},21,12)"
            if not pg and field in ('created_at','updated_at'):
                value=f"replace({field},' ','T')||'Z'"
            values.extend([f"'{field}'",value])
        build='json_build_object' if pg else 'json_object'
        payload=build+'('+','.join(values)+')'
        op.execute(sa.text(f"INSERT INTO sync_changes (id,sequence,kind,facility_id,entity_id,payload,created_at,updated_at) SELECT id,(SELECT sequence FROM sync_clock)+row_number() OVER (ORDER BY id),'{kind}',facility_id,id,{payload},created_at,updated_at FROM {table}"))
        op.execute(sa.text('UPDATE sync_clock SET sequence=(SELECT COALESCE(MAX(sequence),0) FROM sync_changes)'))


def downgrade():
    op.drop_table('sync_changes')
    op.drop_table('sync_clock')
