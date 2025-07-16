"""
Celery application configuration.
"""

from celery import Celery
from config import get_settings

settings = get_settings()

celery_app = Celery(
    "nft_trading_bot",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=['core.tasks']  # Only include core.tasks
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    result_expires=3600,
    task_track_started=True,
    task_time_limit=30 * 60,
    task_soft_time_limit=25 * 60,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)