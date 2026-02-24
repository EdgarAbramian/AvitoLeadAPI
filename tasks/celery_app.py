from celery import Celery
from utils import cfg

celery_app = Celery(
    'avito_lead_api',
    broker=cfg.redis_url,
    backend=cfg.redis_url,
    include=['tasks.lead_tasks']
)

celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    timezone='Europe/Moscow',
    worker_prefetch_multiplier=1,
)
