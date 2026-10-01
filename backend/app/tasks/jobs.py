import asyncio
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker
from sqlalchemy.pool import NullPool
from app.core.config import settings
from app.models.alerts import AlertRule
from app.services.alerts import evaluate_rule,escalate
from app.services.notifications import NotificationService
from app.tasks.celery_app import celery_app


async def run_db(operation):
    engine=create_async_engine(settings.get_database_url(),poolclass=NullPool,hide_parameters=True)
    try:
        async with async_sessionmaker(engine,expire_on_commit=False).begin() as db:
            return await operation(db)
    finally:
        await engine.dispose()


@celery_app.task(name='alerts.evaluate')
def evaluate(identifier):
    return asyncio.run(run_db(lambda db:evaluate_rule(db,UUID(identifier))))


@celery_app.task(name='alerts.dispatch')
def dispatch():
    async def enqueue(db):
        count=0
        rows=await db.stream_scalars(select(AlertRule.id).where(AlertRule.active.is_(True)).execution_options(yield_per=200))
        async for identifier in rows:
            evaluate.delay(str(identifier))
            count+=1
        return count
    return asyncio.run(run_db(enqueue))


@celery_app.task(name='alerts.escalate')
def escalation():
    return asyncio.run(run_db(escalate))


@celery_app.task(name='notifications.deliver')
def deliver():
    return asyncio.run(run_db(NotificationService.deliver_pending))


@celery_app.task(name='reports.schedule')
def scheduled_reports():
    from app.services.report_jobs import due_schedules
    return asyncio.run(run_db(due_schedules))


@celery_app.task(name='reports.generate')
def generate_reports():
    from app.services.report_jobs import generate_pending
    return asyncio.run(run_db(generate_pending))

@celery_app.task(name='reports.expire')
def expire_reports():
    from app.services.report_jobs import expire_artifacts
    return asyncio.run(run_db(expire_artifacts))
