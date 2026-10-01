from datetime import datetime,timezone
from sqlalchemy import select
from app.models import User
from app.models.alerts import NotificationLog
from app.security.scope import check_facility
from app.integrations.notifications import providers


class NotificationService:
    @staticmethod
    async def send(db, *, channel, recipient, template, data, facility_id, dedup_key):
        await check_facility(db,recipient,facility_id)
        existing=await db.scalar(select(NotificationLog).where(NotificationLog.dedup_key==dedup_key))
        if existing:
            return existing
        row=NotificationLog(channel=channel,recipient_id=recipient.id,template=template,payload=data,
                            facility_id=facility_id,dedup_key=dedup_key)
        db.add(row)
        await db.flush()
        return row

    @staticmethod
    async def deliver_pending(db, limit=100):
        rows=await db.scalars(select(NotificationLog).where(NotificationLog.status.in_(['pending','failed']),NotificationLog.attempts<5)
                              .order_by(NotificationLog.created_at).limit(limit).with_for_update(skip_locked=True))
        delivered=0
        for row in rows:
            row.attempts+=1
            recipient=await db.get(User,row.recipient_id)
            try:
                if not recipient or not recipient.active:
                    raise ValueError('Inactive recipient')
                await check_facility(db,recipient,row.facility_id)
                if row.channel!='in-app':
                    provider=providers.get(row.channel)
                    if not provider:
                        row.status,row.failure_reason='failed','PROVIDER_NOT_CONFIGURED'
                        continue
                    await provider.send(recipient_id=row.recipient_id,template=row.template,data=row.payload,idempotency_key=str(row.id))
                row.status,row.failure_reason='delivered',None
                row.delivered_at=datetime.now(timezone.utc)
                delivered+=1
            except Exception:
                # External error text may contain addresses, tokens or credentials.
                row.status,row.failure_reason='failed','DELIVERY_FAILED'
        return delivered
