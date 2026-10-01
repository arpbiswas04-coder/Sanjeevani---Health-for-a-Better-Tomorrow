from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy import select


async def get_record(db, model, identifier, *, lock=False):
    query = select(model).where(model.id == identifier)
    if lock:
        query = query.with_for_update().execution_options(populate_existing=True)
    result = await db.scalar(query)
    if result is None:
        raise HTTPException(404, 'Record not found')
    return result


def serialize(row, exclude=()):
    hidden = {'password_hash', 'token_hash', *exclude}
    result = {}
    for column in row.__table__.columns:
        if column.name in hidden:
            continue
        value = getattr(row, column.name)
        if isinstance(value, datetime):
            value = value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)
        result[column.name] = value
    return result
