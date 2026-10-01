from celery import Celery
from app.core.config import settings

celery_app=Celery('sanjeevani',broker=settings.REDIS_URL,backend=settings.REDIS_URL,include=['app.tasks.jobs'])
celery_app.conf.update(
    task_serializer='json',result_serializer='json',accept_content=['json'],timezone='UTC',enable_utc=True,
    task_acks_late=True,worker_prefetch_multiplier=1,broker_connection_retry_on_startup=True,
    beat_schedule={
        'expire-report-artifacts':{'task':'reports.expire','schedule':3600.0},
        'schedule-reports':{'task':'reports.schedule','schedule':60.0},
        'generate-report':{'task':'reports.generate','schedule':10.0},
        'evaluate-alert-rules':{'task':'alerts.dispatch','schedule':300.0},
        'escalate-alerts':{'task':'alerts.escalate','schedule':60.0},
        'deliver-notifications':{'task':'notifications.deliver','schedule':30.0},
    },
)
