"""Read optional source-location annotations without changing exact geography.

These immutable development provenance annotations are not facility coordinates.
Only attach to already authorized rows; never use them for scope or nearby queries.
"""
from sqlalchemy import select
from app.models import AuditLog
from app.schemas.outputs import ApproximateLocation


async def attach_location_context(db,rows):
    candidates={str(r['id']):r for r in rows if r.get('latitude') is None and r.get('longitude') is None}
    if not candidates:return rows
    annotations=await db.scalars(select(AuditLog.details).where(
        AuditLog.action=='devdata.location.annotated',
        AuditLog.details['facility_id'].as_string().in_(list(candidates))).order_by(AuditLog.created_at,AuditLog.id))
    for entry in annotations:
        row=candidates[entry['facility_id']]
        if row['code']!=entry['code'] or row.get('address')!=entry['address']:continue
        try:context=ApproximateLocation.model_validate(entry['location_context'])
        except ValueError:continue  # Invalid optional provenance cannot break the directory.
        row['location_context']=context.model_dump()
    return rows
