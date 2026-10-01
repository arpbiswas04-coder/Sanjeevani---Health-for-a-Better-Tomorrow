from sqlalchemy import select, update
from fastapi.encoders import jsonable_encoder
from app.models.sync import SyncClock, SyncChange, CLOCK_ID
from app.repositories.common import serialize


async def lock_clock(db):
    # A transactional UPDATE (not nextval) serializes allocation AND commit order.
    # SQLite ignores FOR UPDATE, so use a write on both supported databases.
    if db.bind.dialect.name == 'postgresql':
        from sqlalchemy.dialects.postgresql import insert
    else:
        from sqlalchemy.dialects.sqlite import insert
    await db.execute(insert(SyncClock).values(id=CLOCK_ID, sequence=0).on_conflict_do_nothing(index_elements=['id']))
    await db.execute(update(SyncClock).where(SyncClock.id==CLOCK_ID).values(sequence=SyncClock.sequence))


async def append_change(db, kind, row):
    sequence=await db.scalar(update(SyncClock).where(SyncClock.id==CLOCK_ID)
        .values(sequence=SyncClock.sequence+1).returning(SyncClock.sequence))
    db.add(SyncChange(sequence=sequence,kind=kind,facility_id=row.facility_id,
                      entity_id=row.id,payload=jsonable_encoder(serialize(row))))
    await db.flush()
