from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy import select
from app.models import AuditLog, Facility, Medicine, MedicineBatch, Inventory, StockTransaction


async def lock_resources(db, facility_id, medicine_id):
    # Every stock writer takes these locks in the same order. The medicine lock
    # also serializes batch creation across facilities (including empty stock).
    facility = await db.scalar(select(Facility).where(Facility.id == facility_id).with_for_update())
    if not facility or not facility.active:
        raise HTTPException(404, 'Active facility not found')
    medicine = await db.scalar(select(Medicine).where(Medicine.id == medicine_id).with_for_update())
    if not medicine:
        raise HTTPException(404, 'Medicine not found')


def audit(db, actor_id, action, details):
    db.add(AuditLog(actor_id=actor_id, action=action, details=details))


async def receive(db, payload, actor):
    await lock_resources(db, payload.facility_id, payload.medicine_id)
    if payload.expires_on <= datetime.now(timezone.utc).date():
        raise HTTPException(422, 'Stock must expire after today')
    batch = await db.scalar(select(MedicineBatch).where(
        MedicineBatch.medicine_id == payload.medicine_id,
        MedicineBatch.batch_number == payload.batch_number))
    if batch and (batch.expires_on != payload.expires_on or batch.recalled):
        raise HTTPException(409, 'Batch expiry differs or batch is recalled')
    if not batch:
        batch = MedicineBatch(medicine_id=payload.medicine_id, batch_number=payload.batch_number,
                              expires_on=payload.expires_on)
        db.add(batch)
        await db.flush()
    stock = await db.scalar(select(Inventory).where(
        Inventory.facility_id == payload.facility_id, Inventory.batch_id == batch.id).with_for_update())
    if not stock:
        stock = Inventory(facility_id=payload.facility_id, batch_id=batch.id, quantity=0)
        db.add(stock)
        await db.flush()
    if stock.quantity + payload.quantity > 2_000_000_000:
        raise HTTPException(409, 'Stock quantity limit exceeded')
    stock.quantity += payload.quantity
    db.add(StockTransaction(inventory_id=stock.id, actor_id=actor.id, quantity=payload.quantity,
                            kind='receive', reference=payload.reference))
    audit(db, actor.id, 'inventory.receive', payload.model_dump(mode='json'))
    await db.flush()
    return {'inventory_id': stock.id, 'batch_id': batch.id, 'quantity': stock.quantity}


async def issue(db, payload, actor):
    await lock_resources(db, payload.facility_id, payload.medicine_id)
    rows = (await db.execute(select(Inventory, MedicineBatch).join(MedicineBatch).where(
        Inventory.facility_id == payload.facility_id,
        MedicineBatch.medicine_id == payload.medicine_id,
        MedicineBatch.expires_on > datetime.now(timezone.utc).date(),
        MedicineBatch.recalled.is_(False), Inventory.quantity > 0
    ).order_by(MedicineBatch.expires_on, MedicineBatch.created_at, MedicineBatch.id)
      .with_for_update())).all()
    if sum(stock.quantity for stock, batch in rows) < payload.quantity:
        raise HTTPException(409, 'Insufficient usable stock')
    remaining, allocations = payload.quantity, []
    for stock, batch in rows:
        quantity = min(remaining, stock.quantity)
        stock.quantity -= quantity
        remaining -= quantity
        db.add(StockTransaction(inventory_id=stock.id, actor_id=actor.id, quantity=-quantity,
                                kind='issue', reference=payload.reference))
        allocations.append({'batch_id': batch.id, 'quantity': quantity})
        if remaining == 0:
            break
    audit(db, actor.id, 'inventory.issue', payload.model_dump(mode='json'))
    await db.flush()
    return {'allocations': allocations}
