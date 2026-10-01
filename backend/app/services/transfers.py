from datetime import datetime, timezone
from app.core.time import utc_today
from fastapi import HTTPException
from sqlalchemy import select,func
from app.models import Facility, Medicine, MedicineBatch, Inventory, StockTransaction
from app.models.transfers import TransferRequest, TransferItem, TransferApproval, TransferTracking
from app.repositories.common import get_record, serialize
from app.security.scope import check_facility
from app.services.inventory import audit
from app.services.idempotency import replay, remember


async def lock_transfer_resources(db, transfer, items, require_active=True):
    for identifier in sorted([transfer.source_id, transfer.destination_id]):
        facility = await get_record(db, Facility, identifier, lock=True)
        if require_active and not facility.active:
            raise HTTPException(409, 'Transfer facility is inactive')
    batches = list(await db.scalars(select(MedicineBatch).where(MedicineBatch.id.in_([i.batch_id for i in items]))))
    if len(batches) != len(items):
        raise HTTPException(404, 'Transfer batch not found')
    for medicine_id in sorted({b.medicine_id for b in batches}):
        await get_record(db, Medicine, medicine_id, lock=True)
    # Reload after acquiring the medicine mutex to observe concurrent recall changes.
    for batch in batches:
        await db.refresh(batch)
    return {b.id: b for b in batches}


async def create(db, user, payload):
    await check_facility(db, user, payload.source_id)
    await check_facility(db, user, payload.destination_id)
    for identifier in sorted([payload.source_id, payload.destination_id]):
        await get_record(db, Facility, identifier, lock=True)
    previous = await replay(db, user.id, 'transfer.create', payload)
    if previous is not None:
        return previous
    row = TransferRequest(source_id=payload.source_id, destination_id=payload.destination_id,
                          requested_by=user.id, reference=payload.reference)
    await lock_transfer_resources(db, row, payload.items)
    db.add(row)
    await db.flush()
    for item in payload.items:
        db.add(TransferItem(transfer_id=row.id, **item.model_dump()))
    db.add(TransferTracking(transfer_id=row.id, actor_id=user.id, status=row.status, note='Requested'))
    audit(db, user.id, 'transfer.requested', {'transfer_id': str(row.id)})
    return remember(db, user.id, 'transfer.create', payload, serialize(row))


async def transition(db, user, identifier, payload):
    row = await get_record(db, TransferRequest, identifier, lock=True)
    await check_facility(db, user, row.source_id)
    await check_facility(db, user, row.destination_id)
    transitions = {'approve': (('pending_approval',), 'approved'), 'reject': (('pending_approval',), 'rejected'),
                   'dispatch': (('approved',), 'dispatched'), 'in_transit': (('dispatched',), 'in_transit'),
                   'receive': (('dispatched','in_transit'), 'received'), 'cancel': (('pending_approval','approved'), 'cancelled')}
    allowed, target = transitions[payload.action]
    if row.status not in allowed:
        raise HTTPException(409, 'Invalid transfer state transition')
    from app.models.supply import Shipment
    if payload.action=='cancel' and await db.scalar(select(Shipment.id).where(Shipment.transfer_id==row.id,Shipment.status!='cancelled').limit(1)):
        raise HTTPException(409,'Cancel planned shipments before cancelling the transfer')
    if payload.action=='receive' and await db.scalar(select(Shipment.id).where(Shipment.transfer_id==row.id,Shipment.status.not_in(['arrived','cancelled'])).limit(1)):
        raise HTTPException(409,'Tracked shipments must arrive before transfer receipt')
    items = list(await db.scalars(select(TransferItem).where(TransferItem.transfer_id == row.id).order_by(TransferItem.batch_id)))
    # Cancellation/rejection and inbound recovery must survive deactivation.
    batches = await lock_transfer_resources(db, row, items, require_active=payload.action in ('approve','dispatch'))
    today = utc_today()
    if payload.action=='approve':
        from app.models.stock import StockPolicy
        requested={}
        for item in items:
            medicine_id=batches[item.batch_id].medicine_id
            requested[medicine_id]=requested.get(medicine_id,0)+item.quantity
        for medicine_id,quantity in requested.items():
            safety=await db.scalar(select(StockPolicy.safety_stock).where(StockPolicy.facility_id==row.source_id,StockPolicy.medicine_id==medicine_id)) or 0
            usable=await db.scalar(select(func.coalesce(func.sum(Inventory.quantity-Inventory.reserved),0)).join(MedicineBatch).where(
                Inventory.facility_id==row.source_id,MedicineBatch.medicine_id==medicine_id,
                MedicineBatch.recalled.is_(False),MedicineBatch.expires_on>today))
            if usable-quantity<safety:
                raise HTTPException(409,'Transfer would breach required safety stock')
    for item in items:
        batch = batches[item.batch_id]
        source = await db.scalar(select(Inventory).where(Inventory.facility_id == row.source_id, Inventory.batch_id == item.batch_id).with_for_update())
        if payload.action in ('approve', 'dispatch') and (batch.recalled or batch.expires_on <= today):
            raise HTTPException(409, 'Transfer batch is expired or recalled')
        if payload.action == 'approve':
            if not source or source.quantity - source.reserved < item.quantity:
                raise HTTPException(409, 'Insufficient available stock')
            source.reserved += item.quantity
        elif payload.action == 'cancel' and row.status == 'approved':
            source.reserved -= item.quantity
        elif payload.action == 'dispatch':
            if not source or source.reserved < item.quantity or source.quantity < item.quantity:
                raise HTTPException(409, 'Reserved stock is unavailable')
            source.quantity -= item.quantity
            source.reserved -= item.quantity
            db.add(StockTransaction(inventory_id=source.id, actor_id=user.id, quantity=-item.quantity,
                                    kind='TRANSFER_OUT', reference=str(row.id)))
        elif payload.action == 'receive':
            destination = await db.scalar(select(Inventory).where(Inventory.facility_id == row.destination_id,
                                                                   Inventory.batch_id == item.batch_id).with_for_update())
            if not destination:
                destination = Inventory(facility_id=row.destination_id, batch_id=item.batch_id, quantity=0, reserved=0)
                db.add(destination)
                await db.flush()
            if destination.quantity + item.quantity > 2_000_000_000:
                raise HTTPException(409, 'Destination quantity limit exceeded')
            from app.services.supply import link_warehouse
            await link_warehouse(db, destination)
            destination.quantity += item.quantity
            db.add(StockTransaction(inventory_id=destination.id, actor_id=user.id, quantity=item.quantity,
                                    kind='TRANSFER_IN', reference=str(row.id)))
    if payload.action in ('approve','reject'):
        db.add(TransferApproval(transfer_id=row.id, actor_id=user.id, decision=target, reason=payload.reason))
    row.status = target
    db.add(TransferTracking(transfer_id=row.id, actor_id=user.id, status=target, note=payload.reason))
    audit(db, user.id, 'transfer.' + payload.action, {'transfer_id': str(row.id)})
    await db.flush()
    return serialize(row)
