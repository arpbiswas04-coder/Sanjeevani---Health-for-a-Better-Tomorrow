from fastapi import HTTPException
from sqlalchemy import select, func, cast
from sqlalchemy.types import UserDefinedType
from app.models import Facility
from app.models.geography import Country, State, District, Block
from app.repositories.common import get_record, serialize
from app.security.scope import check_facility, facility_filter
from app.services.inventory import audit

GEOGRAPHIES = {'countries': (Country, None, None), 'states': (State, Country, 'country_id'),
               'districts': (District, State, 'state_id'), 'blocks': (Block, District, 'district_id')}


class GeographyType(UserDefinedType):
    cache_ok = True
    def get_col_spec(self, **kw):
        return 'geography'


async def create_geography(db, user, kind, payload):
    if kind not in GEOGRAPHIES:
        raise HTTPException(404, 'Unknown geography level')
    model, parent, field = GEOGRAPHIES[kind]
    values = {'name': payload.name, 'code': payload.code}
    if parent:
        await get_record(db, parent, payload.parent_id)
        values[field] = payload.parent_id
    elif payload.parent_id:
        raise HTTPException(422, 'Country cannot have a parent')
    row = model(**values)
    db.add(row)
    await db.flush()
    audit(db, user.id, 'geography.created', {'kind': kind, 'id': str(row.id)})
    return serialize(row)


async def update_facility(db, user, identifier, payload):
    await check_facility(db, user, identifier)
    row = await get_record(db, Facility, identifier, lock=True)
    values = payload.model_dump(exclude_unset=True)
    if any(values.get(k) is None for k in ('name', 'facility_type', 'active') if k in values):
        raise HTTPException(422, 'Required fields cannot be null')
    if values.get('block_id'):
        await get_record(db, Block, values['block_id'])
    for name, value in values.items():
        setattr(row, name, value)
    from app.models.supply import Warehouse
    warehouse=await db.scalar(select(Warehouse).where(Warehouse.facility_id==row.id).with_for_update())
    if warehouse:
        if row.facility_type!='warehouse':
            raise HTTPException(409,'Warehouse facilities must retain their warehouse type')
        warehouse.active=row.active
    row.version += 1
    audit(db, user.id, 'facility.updated', {'id': str(row.id), 'fields': list(values)})
    await db.flush()
    return serialize(row)


async def list_facilities(db, user, offset=0, limit=50, search=None, block_id=None,
                          district_id=None, state_id=None, country_id=None, active=True):
    query = select(Facility).where(facility_filter(user, Facility.id))
    if active is not None:
        query = query.where(Facility.active == active)
    if search:
        query = query.where(Facility.name.ilike('%' + search + '%'))
    if block_id:
        query = query.where(Facility.block_id == block_id)
    if district_id or state_id or country_id:
        query = query.join(Block, Facility.block_id == Block.id).join(District).join(State)
        if district_id:
            query = query.where(District.id == district_id)
        if state_id:
            query = query.where(State.id == state_id)
        if country_id:
            query = query.where(State.country_id == country_id)
    from app.services.location_context import attach_location_context
    rows=[serialize(row) for row in await db.scalars(query.order_by(Facility.id).offset(offset).limit(limit))]
    return await attach_location_context(db,rows)


async def nearby(db, user, latitude, longitude, radius_km, limit):
    if db.bind.dialect.name == 'postgresql':
        origin = cast(func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326), GeographyType())
        location = cast(func.ST_SetSRID(func.ST_MakePoint(Facility.longitude, Facility.latitude), 4326), GeographyType())
        distance = func.ST_Distance(location, origin) / 1000
        within = func.ST_DWithin(location, origin, radius_km * 1000)
    else:
        # Test/development spherical approximation; production uses PostGIS geodesics.
        lat1, lat2 = func.radians(latitude), func.radians(Facility.latitude)
        dlat, dlon = lat2 - lat1, func.radians(Facility.longitude - longitude)
        a = func.pow(func.sin(dlat / 2), 2) + func.cos(lat1) * func.cos(lat2) * func.pow(func.sin(dlon / 2), 2)
        distance = 6371 * 2 * func.asin(func.sqrt(func.min(1.0, a)))
        within = distance <= radius_km
    rows = await db.execute(select(Facility, distance.label('distance_km')).where(
        Facility.active.is_(True), Facility.latitude.is_not(None), Facility.longitude.is_not(None),
        facility_filter(user, Facility.id), within).order_by(distance, Facility.id).limit(limit))
    return [{**serialize(row), 'distance_km': km} for row, km in rows]
