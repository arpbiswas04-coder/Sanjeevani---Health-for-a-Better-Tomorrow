from hashlib import sha256
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from app.models.stock import MutationReceipt


async def replay(db, user_id, operation, payload):
    key = getattr(payload, 'idempotency_key', None)
    if not key:
        return None
    row = await db.scalar(select(MutationReceipt).where(MutationReceipt.actor_id == user_id,
                         MutationReceipt.operation == operation, MutationReceipt.key == key))
    if row:
        if row.request_hash != sha256(payload.model_dump_json().encode()).hexdigest():
            raise HTTPException(409, 'Idempotency key reused with different input')
        return row.response


def remember(db, user_id, operation, payload, response):
    key = getattr(payload, 'idempotency_key', None)
    if key:
        db.add(MutationReceipt(actor_id=user_id, operation=operation, key=key,
              request_hash=sha256(payload.model_dump_json().encode()).hexdigest(), response=jsonable_encoder(response)))
    return response
