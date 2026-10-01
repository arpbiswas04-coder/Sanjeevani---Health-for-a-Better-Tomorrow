from datetime import datetime, timezone, timedelta
from math import ceil
from app.core.time import utc_today
from fastapi import HTTPException
from sqlalchemy import select, func
from app.models import MedicineBatch, Inventory, StockTransaction
from app.models.stock import StockPolicy, RecallRecord, ExpiryRecord
from app.repositories.common import get_record, serialize
from app.security.scope import check_facility, facility_filter
from app.services.inventory import lock_resources, audit
from app.services.idempotency import replay, remember


async def adjust(db, user, payload):
    await check_facility(db, user, payload.facility_id)
    batch = await get_record(db, MedicineBatch, payload.batch_id)
    await lock_resources(db, payload.facility_id, batch.medicine_id)
    previous = await replay(db, user.id, 'adjust', payload)
    if previous is not None:
        return previous
    batch = await get_record(db, MedicineBatch, payload.batch_id, lock=True)
    await db.refresh(batch)
    today = utc_today()
    if payload.quantity > 0 and (batch.recalled or batch.expires_on <= today):
        raise HTTPException(409, 'Cannot add unusable stock')
    if payload.kind == 'EXPIRED' and batch.expires_on > today:
        raise HTTPException(409, 'Batch has not expired')
    if payload.kind == 'RECALL' and not batch.recalled:
        raise HTTPException(409, 'Batch is not recalled')
    stock = await db.scalar(select(Inventory).where(Inventory.facility_id == payload.facility_id, Inventory.batch_id == batch.id).with_for_update())
    if not stock:
        raise HTTPException(404, 'Inventory not found')
    if not stock.reserved <= stock.quantity + payload.quantity <= 2_000_000_000:
        raise HTTPException(409, 'Adjustment exceeds unreserved stock or storage limit')
    stock.quantity += payload.quantity
    transaction = StockTransaction(inventory_id=stock.id, actor_id=user.id, quantity=payload.quantity, kind=payload.kind, reference=payload.reference)
    db.add(transaction)
    await db.flush()
    if payload.kind == 'EXPIRED':
        db.add(ExpiryRecord(inventory_id=stock.id, transaction_id=transaction.id, quantity=-payload.quantity))
    audit(db, user.id, 'inventory.adjust', payload.model_dump(mode='json'))
    return remember(db, user.id, 'adjust', payload, {'inventory_id': stock.id, 'quantity': stock.quantity})


async def set_policy(db, user, facility_id, medicine_id, payload):
    await check_facility(db, user, facility_id)
    await lock_resources(db, facility_id, medicine_id)
    policy = await db.scalar(select(StockPolicy).where(StockPolicy.facility_id == facility_id, StockPolicy.medicine_id == medicine_id))
    if not policy:
        policy = StockPolicy(facility_id=facility_id, medicine_id=medicine_id)
        db.add(policy)
    for key, value in payload.model_dump().items():
        setattr(policy, key, value)
    audit(db, user.id, 'inventory.policy_updated', {'facility_id': str(facility_id), 'medicine_id': str(medicine_id)})
    await db.flush()
    return serialize(policy)


async def days_of_stock(db, user, facility_id, medicine_id, window=30):
    await check_facility(db, user, facility_id)
    policy = await db.scalar(select(StockPolicy).where(StockPolicy.facility_id == facility_id, StockPolicy.medicine_id == medicine_id))
    now = datetime.now(timezone.utc)
    current = await db.scalar(select(func.coalesce(func.sum(Inventory.quantity - Inventory.reserved), 0)).join(MedicineBatch).where(
        Inventory.facility_id == facility_id, MedicineBatch.medicine_id == medicine_id,
        MedicineBatch.recalled.is_(False), MedicineBatch.expires_on > now.date()))
    base = select(StockTransaction).join(Inventory).join(MedicineBatch).where(Inventory.facility_id == facility_id, MedicineBatch.medicine_id == medicine_id)
    first = await db.scalar(base.with_only_columns(func.min(StockTransaction.created_at)))
    consumed = -(await db.scalar(base.with_only_columns(func.coalesce(func.sum(StockTransaction.quantity), 0)).where(
        StockTransaction.kind == 'issue', StockTransaction.created_at >= now - timedelta(days=window))))
    if first and first.tzinfo is None:
        first = first.replace(tzinfo=timezone.utc)
    history_days = min(window, max(1, (now.date() - first.date()).days + 1)) if first else 0
    minimum = policy.minimum_history_days if policy else 7
    rate = consumed / history_days if history_days else None
    dos = current / rate if rate and history_days >= minimum else None
    status = 'no_history' if not first else 'insufficient_history' if history_days < minimum else 'zero_consumption' if rate == 0 else 'normal'
    if dos is not None:
        status = 'critical' if dos <= (policy.critical_days if policy else 3) else 'low' if dos <= (policy.low_days if policy else 7) else 'normal'
    safety, lead = (policy.safety_stock, policy.lead_days) if policy else (0, 7)
    reorder_point = ceil(rate * lead + safety) if rate is not None and history_days >= minimum else None
    return {'current_stock': current, 'average_daily_consumption': rate, 'days_of_stock': dos,
            'history_days': history_days, 'status': status, 'safety_stock': safety,
            'transferable_stock': max(0, current - safety),
            'reorder_point': reorder_point, 'suggested_quantity': max(0, reorder_point - current) if reorder_point is not None else None}


async def recall(db, user, payload):
    batch = await get_record(db, MedicineBatch, payload.batch_id)
    # Same medicine mutex as every inventory writer. Global recall affects all facilities.
    from app.models import Medicine
    await get_record(db, Medicine, batch.medicine_id, lock=True)
    batch = await get_record(db, MedicineBatch, payload.batch_id, lock=True)
    if batch.recalled:
        raise HTTPException(409, 'Batch already recalled')
    batch.recalled = True
    record = RecallRecord(**payload.model_dump(), initiated_by=user.id)
    db.add(record)
    await db.flush()
    audit(db, user.id, 'inventory.recall', {'recall_id': str(record.id), 'batch_id': str(batch.id)})
    return serialize(record)


async def trace(db, user, batch_id, offset, limit):
    batch = await get_record(db, MedicineBatch, batch_id)
    stocks = await db.scalars(select(Inventory).where(Inventory.batch_id == batch_id, facility_filter(user, Inventory.facility_id)).order_by(Inventory.id).offset(offset).limit(limit))
    transactions = await db.scalars(select(StockTransaction).join(Inventory).where(Inventory.batch_id == batch_id,
        facility_filter(user, Inventory.facility_id)).order_by(StockTransaction.created_at, StockTransaction.id).offset(offset).limit(limit))
    return {'batch': serialize(batch), 'inventory': [serialize(row) for row in stocks], 'transactions': [serialize(row) for row in transactions]}


async def expiry_rows(db,user,facility_id,days=None,offset=0,limit=200):
    await check_facility(db,user,facility_id)
    from sqlalchemy import and_
    query=select(Inventory,MedicineBatch).join(MedicineBatch).outerjoin(StockPolicy,and_(
        StockPolicy.facility_id==Inventory.facility_id,StockPolicy.medicine_id==MedicineBatch.medicine_id))
    warning=days if days is not None else func.coalesce(StockPolicy.expiry_warning_days,90)
    cutoff=expiry_cutoff(db,warning)
    rows=await db.execute(query.where(Inventory.facility_id==facility_id,Inventory.quantity>0,
        MedicineBatch.expires_on<=cutoff).order_by(MedicineBatch.expires_on,Inventory.id).offset(offset).limit(limit))
    return [{'inventory':serialize(i),'batch':serialize(b),'state':'expired' if b.expires_on<=utc_today() else 'upcoming'} for i,b in rows]


def expiry_cutoff(db,days):
    from sqlalchemy import literal
    if db.bind.dialect.name=='postgresql':
        return literal(utc_today())+days
    return func.date(str(utc_today()),func.printf('+%d days',days))
