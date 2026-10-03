"""Bounded, offline enrichment of an existing owned development seed.

Location annotations live in immutable audit provenance, NOT Facility latitude/
longitude. Approximate city points must never enter PostGIS nearby/routing queries.
No network requests, credentials, imports or startup hooks in this module.
"""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
from uuid import UUID
from sqlalchemy import select
from app.models import (AuditLog, Facility, Equipment, Ambulance, MutationReceipt,
                        Supplier, PurchaseOrderItem)
from app.services import assets, operations, supply
from app.services.inventory import audit
from app.schemas.assets import AmbulanceInput, MaintenanceInput
from app.schemas.operations import TemperatureInput
from app.schemas.supply import OrderInput, OrderAction, ShipmentInput, ShipmentAction, OrderReceipt
from scripts.development_data import clean, STATES

REFERENCES=Path(__file__).parent/'data/development_city_references.json'
LOCATION_ACTION='devdata.location.annotated'


async def annotate_locations(db,user,reference):
    index={(clean(r['city']).casefold(),clean(r['state']).casefold()):r for r in reference['cities']}
    if len(index)!=len(reference['cities']):raise ValueError('Ambiguous city reference')
    # Bound the tool to the first verified 50 imported facilities. No bulk geocoding.
    sources=list(await db.scalars(select(AuditLog.details).where(
        AuditLog.action=='devdata.facilities.imported').order_by(AuditLog.created_at,AuditLog.id).limit(50)))
    existing=set(await db.scalars(select(AuditLog.details['facility_id'].as_string()).where(AuditLog.action==LOCATION_ACTION)))
    count=0
    for source in sources:
        point=index.get((clean(source['city']).casefold(),clean(source['state']).casefold()))
        if not point or source['id'] in existing:continue
        facility=await db.get(Facility,UUID(source['id']))
        if not facility or not facility.active or facility.code!=source['code'] or not facility.code.startswith('FD1-'):continue
        if facility.latitude is not None or facility.longitude is not None:continue
        state=next((s for s in STATES if s.casefold()==clean(source['state']).casefold()),clean(source['state']))
        address='; '.join(v for v in [clean(source['city']),('PIN '+clean(source['pincode'])) if clean(source['pincode']) else '',state] if v)
        if clean(facility.address)!=address:continue  # A reviewed/moved facility must not inherit a stale source point.
        if not (-90<=point['latitude']<=90 and -180<=point['longitude']<=180):raise ValueError('Invalid reference point')
        audit(db,user.id,LOCATION_ACTION,{'facility_id':str(facility.id),'code':facility.code,
            'address':facility.address,'source_sha256':source['source_sha256'],
            'location_context':{'precision':'approximate_city','city':point['city'],'state':point['state'],
                'latitude':point['latitude'],'longitude':point['longitude'],'reference_id':point['reference_id'],
                'source_url':point['source_url'],'dataset_sha256':reference['dataset_sha256'],
                'retrieved_on':reference['retrieved_on'],'attribution':'GeoNames, CC BY 4.0'}})
        existing.add(source['id']);count+=1
    await db.flush()
    return count


async def enrich(db,user,seed):
    base=await db.scalar(select(MutationReceipt).where(MutationReceipt.actor_id==user.id,
        MutationReceipt.operation=='devdata.operations',MutationReceipt.key==str(seed)))
    if not base:raise ValueError('Run the owned operations seed first')
    source=REFERENCES.read_bytes();fingerprint=sha256(source).hexdigest()
    previous=await db.scalar(select(MutationReceipt).where(MutationReceipt.actor_id==user.id,
        MutationReceipt.operation=='devdata.enrichment.v1',MutationReceipt.key==str(seed)))
    if previous:
        if previous.request_hash!=fingerprint:raise ValueError('Reference snapshot changed; review before further enrichment')
        return {**previous.response,'reused':True}
    manifest=base.response;ids=[UUID(v) for v in manifest['facility_ids']]
    prefix=f'DEVOPS-{seed}';extra=prefix+'-ENRICH'
    for identifier in ids:
        facility=await db.get(Facility,identifier)
        if not facility or not facility.active or not facility.code.startswith('FD1-'):raise ValueError('Source seed facility changed')
    now=datetime.now(timezone.utc);today=now.date()
    locations=await annotate_locations(db,user,json.loads(source))
    for i,identifier in enumerate(ids):
        await assets.save(db,user,Ambulance,AmbulanceInput(facility_id=identifier,
            vehicle_id=f'{extra}-AMB-{i}',status='available',operational=True))
        equipment=await db.scalar(select(Equipment).where(Equipment.facility_id==identifier,Equipment.code==f'{prefix}-EQ-{i}'))
        if not equipment or equipment.last_maintenance:raise ValueError('Seed equipment changed; refusing to overwrite maintenance history')
        await assets.maintain(db,user,equipment.id,MaintenanceInput(performed_on=today,
            next_due=today+timedelta(days=30),notes=extra+' SYNTHETIC maintenance, not a real inspection'))
    supplier=await db.scalar(select(Supplier).where(Supplier.code==prefix+'-SUP'))
    if not supplier or not supplier.active:raise ValueError('Owned supplier missing or inactive')
    medicine=UUID(manifest['medicine_ids'][-1])
    order=await supply.order_create(db,user,OrderInput(reference=extra+'-PO',supplier_id=supplier.id,
        facility_id=ids[0],items=[{'medicine_id':medicine,'quantity':10,'unit_price':'1.00'}]))
    for action in ('submit','approve','order'):
        await supply.order_action(db,user,order['id'],OrderAction(action=action,note=extra+' SYNTHETIC workflow'))
    shipment=await supply.shipment_create(db,user,ShipmentInput(reference=extra+'-SHIP',order_id=order['id'],
        origin=extra+' SYNTHETIC depot',expected_at=now+timedelta(days=1),carrier='DEVELOPMENT ONLY'))
    for status in ('dispatched','in_transit','arrived'):
        await supply.shipment_action(db,user,shipment['id'],ShipmentAction(status=status,note=extra+' SYNTHETIC workflow'))
    item=await db.scalar(select(PurchaseOrderItem).where(PurchaseOrderItem.order_id==order['id']))
    await supply.order_receive(db,user,order['id'],OrderReceipt(item_id=item.id,batch_number=extra+'-LOT',
        expires_on=today+timedelta(days=180),quantity=10,idempotency_key=extra+'-receive'))
    for i,temperature in enumerate([4,10]):
        await operations.temperature(db,user,TemperatureInput(facility_id=ids[0],shipment_id=shipment['id'],
            observed_at=now-timedelta(minutes=2-i),temperature=temperature,minimum=2,maximum=8,
            source=extra+'-SYNTHETIC',external_id=str(i)))
    result={'seed':seed,'reused':False,'as_of':str(today),'approximate_locations_added':locations,
        'ambulances_added':len(ids),'maintenance_added':len(ids),'order_id':str(order['id']),
        'shipment_id':str(shipment['id']),'temperature_observations_added':2}
    db.add(MutationReceipt(actor_id=user.id,operation='devdata.enrichment.v1',key=str(seed),request_hash=fingerprint,response=result))
    audit(db,user.id,'devdata.enrichment.completed',result)
    await db.flush()
    return result
