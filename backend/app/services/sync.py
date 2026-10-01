from datetime import datetime,timezone
from sqlalchemy import select,and_,or_
from fastapi import HTTPException
from app.models import User,Facility
from app.models.operations import PatientFootfall,DiseaseCount
from app.repositories.common import get_record,serialize
from app.security.scope import check_facility,facility_filter
from app.services.idempotency import replay,remember
from app.services.operations import aggregate


async def push(db,user,payload):
    from app.services.sync_log import lock_clock
    await lock_clock(db)
    # Serializes idempotency keys even when requests touch different facilities.
    await get_record(db,User,user.id,lock=True)
    for identifier in sorted({i.payload.facility_id for i in payload.items}):
        await check_facility(db,user,identifier)
        await get_record(db,Facility,identifier,lock=True)
    previous=await replay(db,user.id,'sync.push',payload)
    if previous is not None:
        return previous
    results=[]
    for item in payload.items:
        results.append(await aggregate(db,user,item.kind,item.payload))
    return remember(db,user.id,'sync.push',payload,{'results':results})


async def pull(db,user,kind,after_sequence,until_sequence,limit):
    from app.models.sync import SyncClock,SyncChange,CLOCK_ID
    committed=await db.scalar(select(SyncClock.sequence).where(SyncClock.id==CLOCK_ID)) or 0
    ceiling=committed if until_sequence is None else until_sequence
    if after_sequence>ceiling or ceiling>committed:
        raise HTTPException(422,'Invalid sync sequence range')
    rows=list(await db.scalars(select(SyncChange).where(facility_filter(user,SyncChange.facility_id),
        SyncChange.kind==kind,SyncChange.sequence>after_sequence,SyncChange.sequence<=ceiling)
        .order_by(SyncChange.sequence).limit(limit+1)))
    more=len(rows)>limit
    results=[{**row.payload,'change_sequence':row.sequence} for row in rows[:limit]]
    cursor={'after_sequence':rows[limit-1].sequence,'until_sequence':ceiling} if more else None
    return {'items':results,'next_cursor':cursor,'watermark':ceiling,'has_more':more}
