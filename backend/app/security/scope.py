from fastapi import HTTPException
from sqlalchemy import select, or_
from app.models import Facility
from app.models.identity import UserFacility, UserDistrict
from app.models.geography import Block


def facility_filter(user, column):
    if user.scope_mode == 'global':
        return True
    explicit = select(UserFacility.facility_id).where(UserFacility.user_id == user.id)
    regional = select(Facility.id).join(Block, Facility.block_id == Block.id).where(
        Block.district_id.in_(select(UserDistrict.district_id).where(UserDistrict.user_id == user.id)))
    return or_(column.in_(explicit), column.in_(regional))


async def check_facility(db, user, facility_id):
    exists = await db.scalar(select(Facility.id).where(Facility.id == facility_id, facility_filter(user, Facility.id)))
    if not exists:
        raise HTTPException(404, 'Facility not found or outside assigned scope')


def global_only(user):
    if user.scope_mode != 'global':
        raise HTTPException(403, 'Global scope required for this operation')
