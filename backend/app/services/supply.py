from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy import select, func, or_, and_, case
from app.models import Facility, Medicine, Inventory
from app.models.supply import Supplier, Warehouse, WarehouseInventory, PurchaseOrder, PurchaseOrderItem, ProcurementHistory, Shipment, ShipmentHistory
from app.models.transfers import TransferRequest
from app.repositories.common import get_record, serialize
from app.security.scope import check_facility, facility_filter
from app.services.inventory import audit, receive
from app.services.idempotency import replay, remember
from app.schemas.platform import Receive


async def supplier_save(db, user, payload, identifier=None):
    row = await get_record(db, Supplier, identifier, lock=True) if identifier else Supplier()
    for key, value in payload.model_dump().items():
        setattr(row, key, value)
    db.add(row)
    await db.flush()
    audit(db, user.id, 'supplier.saved', {'id': str(row.id)})
    return serialize(row)


async def metrics(db, supplier_id):
    await get_record(db, Supplier, supplier_id)
    count = await db.scalar(select(func.count()).select_from(PurchaseOrder).where(PurchaseOrder.supplier_id == supplier_id))
    eligible=await db.scalar(select(func.count()).select_from(PurchaseOrder).where(PurchaseOrder.supplier_id==supplier_id,PurchaseOrder.status.in_(['ordered','partially_received','received'])))
    complete = await db.scalar(select(func.count()).select_from(PurchaseOrder).where(PurchaseOrder.supplier_id == supplier_id, PurchaseOrder.status == 'received'))
    ordered, received = (await db.execute(select(func.coalesce(func.sum(PurchaseOrderItem.quantity),0),func.coalesce(func.sum(PurchaseOrderItem.received),0))
        .join(PurchaseOrder).where(PurchaseOrder.supplier_id == supplier_id, PurchaseOrder.status.in_(['ordered','partially_received','received'])))).one()
    # Aggregate delay in SQL to avoid loading shipment histories into memory.
    if db.bind.dialect.name == 'postgresql':
        delay = func.extract('epoch', Shipment.arrived_at - Shipment.expected_at) / 86400
    else:
        delay = func.julianday(Shipment.arrived_at) - func.julianday(Shipment.expected_at)
    avg = await db.scalar(select(func.avg(case((delay>0,delay),else_=0))).where(Shipment.supplier_id == supplier_id, Shipment.arrived_at.is_not(None),Shipment.expected_at.is_not(None)))
    return {'order_count':count,'eligible_order_count':eligible,'fulfilment_rate':complete/eligible if eligible else None,
            'quantity_fulfilment_rate':received/ordered if ordered else None,'average_delivery_delay_days':avg}


async def warehouse_create(db, user, payload):
    await check_facility(db,user,payload.facility_id)
    facility = await get_record(db,Facility,payload.facility_id,lock=True)
    facility.facility_type = 'warehouse'
    row = Warehouse(facility_id=facility.id, active=facility.active, capacity={'units':payload.capacity_units,'cold_storage':payload.cold_storage})
    db.add(row)
    await db.flush()
    existing = await db.scalars(select(Inventory).where(Inventory.facility_id == facility.id))
    for stock in existing:
        db.add(WarehouseInventory(warehouse_id=row.id,inventory_id=stock.id))
    audit(db,user.id,'warehouse.created',{'id':str(row.id)})
    return serialize(row)


async def link_warehouse(db, stock):
    warehouse = await db.scalar(select(Warehouse).where(Warehouse.facility_id == stock.facility_id))
    if warehouse and not await db.scalar(select(WarehouseInventory.id).where(WarehouseInventory.inventory_id == stock.id)):
        db.add(WarehouseInventory(warehouse_id=warehouse.id, inventory_id=stock.id))


async def order_create(db,user,payload):
    await check_facility(db,user,payload.facility_id)
    supplier = await get_record(db,Supplier,payload.supplier_id)
    if not supplier.active:
        raise HTTPException(409,'Supplier is inactive')
    row = PurchaseOrder(reference=payload.reference,supplier_id=supplier.id,facility_id=payload.facility_id,created_by=user.id)
    db.add(row)
    await db.flush()
    for item in payload.items:
        await get_record(db,Medicine,item.medicine_id)
        db.add(PurchaseOrderItem(order_id=row.id,**item.model_dump()))
    db.add(ProcurementHistory(order_id=row.id,actor_id=user.id,status='draft',note='Created'))
    audit(db,user.id,'procurement.created',{'id':str(row.id)})
    return serialize(row)


async def order_action(db,user,identifier,payload):
    row = await get_record(db,PurchaseOrder,identifier,lock=True)
    await check_facility(db,user,row.facility_id)
    transitions = {'submit':(('draft',),'submitted'),'approve':(('submitted',),'approved'),
                   'order':(('approved',),'ordered'),'cancel':(('draft','submitted','approved','ordered'),'cancelled')}
    allowed,target = transitions[payload.action]
    if row.status not in allowed:
        raise HTTPException(409,'Invalid purchase order transition')
    if payload.action=='cancel' and await db.scalar(select(Shipment.id).where(Shipment.order_id==row.id,Shipment.status!='cancelled').limit(1)):
        raise HTTPException(409,'Cancel planned shipments first; dispatched or arrived shipments require completion')
    row.status = target
    db.add(ProcurementHistory(order_id=row.id,actor_id=user.id,status=target,note=payload.note))
    audit(db,user.id,'procurement.'+payload.action,{'id':str(row.id)})
    await db.flush()
    return serialize(row)


async def order_receive(db,user,identifier,payload):
    row = await get_record(db,PurchaseOrder,identifier,lock=True)
    await check_facility(db,user,row.facility_id)
    previous = await replay(db,user.id,'procurement.receive.'+str(identifier),payload)
    if previous is not None:
        return previous
    if row.status not in ('ordered','partially_received'):
        raise HTTPException(409,'Order is not receivable')
    if await db.scalar(select(Shipment.id).where(Shipment.order_id==row.id,Shipment.status.not_in(['arrived','cancelled'])).limit(1)):
        raise HTTPException(409,'Tracked shipments must arrive before receipt')
    item = await get_record(db,PurchaseOrderItem,payload.item_id,lock=True)
    if item.order_id != row.id:
        raise HTTPException(404,'Order item not found')
    if item.received + payload.quantity > item.quantity:
        raise HTTPException(409,'Receipt exceeds ordered quantity')
    result = await receive(db,Receive(facility_id=row.facility_id,medicine_id=item.medicine_id,
        batch_number=payload.batch_number,expires_on=payload.expires_on,quantity=payload.quantity,reference=str(row.id)),user)
    item.received += payload.quantity
    await db.flush()
    remaining = await db.scalar(select(func.sum(PurchaseOrderItem.quantity-PurchaseOrderItem.received)).where(PurchaseOrderItem.order_id == row.id))
    row.status = 'received' if remaining == 0 else 'partially_received'
    db.add(ProcurementHistory(order_id=row.id,actor_id=user.id,status=row.status,note='Stock received'))
    audit(db,user.id,'procurement.received',{'id':str(row.id),'item_id':str(item.id)})
    return remember(db,user.id,'procurement.receive.'+str(identifier),payload,{'order':serialize(row),'stock':result})


async def shipment_create(db,user,payload):
    source = await get_record(db,PurchaseOrder if payload.order_id else TransferRequest,payload.order_id or payload.transfer_id,lock=True)
    valid=('ordered','partially_received') if payload.order_id else ('approved','dispatched','in_transit')
    if source.status not in valid:
        raise HTTPException(409,'Source is not eligible for a new shipment')
    facility_id = source.facility_id if payload.order_id else source.destination_id
    await check_facility(db,user,facility_id)
    if payload.transfer_id:
        await check_facility(db,user,source.source_id)
    row = Shipment(reference=payload.reference,order_id=payload.order_id,transfer_id=payload.transfer_id,
        supplier_id=source.supplier_id if payload.order_id else None,facility_id=facility_id,origin=payload.origin,
        expected_at=payload.expected_at,transport={'vehicle':payload.vehicle,'carrier':payload.carrier})
    db.add(row)
    await db.flush()
    db.add(ShipmentHistory(shipment_id=row.id,actor_id=user.id,status='planned',note='Created'))
    audit(db,user.id,'shipment.created',{'id':str(row.id)})
    return serialize(row)


async def shipment_action(db,user,identifier,payload):
    row = await get_record(db,Shipment,identifier)
    parent=await get_record(db,PurchaseOrder if row.order_id else TransferRequest,row.order_id or row.transfer_id,lock=True)
    row = await get_record(db,Shipment,identifier,lock=True)
    await check_shipment_scope(db,user,row)
    if payload.status!='cancelled':
        valid=('ordered','partially_received') if row.order_id else ('dispatched','in_transit','received')
        if parent.status not in valid:
            raise HTTPException(409,'Source state does not permit shipment movement')
    allowed = {'planned':('dispatched','cancelled'),'dispatched':('in_transit','arrived'), 'in_transit':('arrived',)}
    if payload.status not in allowed.get(row.status,()):
        raise HTTPException(409,'Invalid shipment transition')
    row.status = payload.status
    if row.status == 'dispatched':
        row.dispatched_at = datetime.now(timezone.utc)
    if row.status == 'arrived':
        row.arrived_at = datetime.now(timezone.utc)
    db.add(ShipmentHistory(shipment_id=row.id,actor_id=user.id,status=row.status,note=payload.note))
    audit(db,user.id,'shipment.'+row.status,{'id':str(row.id)})
    await db.flush()
    return serialize(row)

async def warehouse_update(db,user,identifier,payload):
    row=await get_record(db,Warehouse,identifier)
    await check_facility(db,user,row.facility_id)
    facility=await get_record(db,Facility,row.facility_id,lock=True)
    row=await get_record(db,Warehouse,identifier,lock=True)
    row.active=payload.active
    facility.active=payload.active
    facility.version+=1
    row.capacity={'units':payload.capacity_units,'cold_storage':payload.cold_storage}
    audit(db,user.id,'warehouse.updated',{'id':str(row.id),'active':row.active})
    await db.flush()
    return serialize(row)


def shipment_scope(user):
    transfers=select(TransferRequest.id).where(facility_filter(user,TransferRequest.source_id),facility_filter(user,TransferRequest.destination_id))
    return and_(facility_filter(user,Shipment.facility_id),or_(Shipment.transfer_id.is_(None),Shipment.transfer_id.in_(transfers)))


async def check_shipment_scope(db,user,row):
    await check_facility(db,user,row.facility_id)
    if row.transfer_id:
        transfer=await get_record(db,TransferRequest,row.transfer_id)
        await check_facility(db,user,transfer.source_id)
        await check_facility(db,user,transfer.destination_id)
