import os
from celery import Celery
import environ #type:ignore
from pathlib import Path #type:ignore

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))
redis_url = env('REDIS_URL')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ClassLens_DB.settings')

app = Celery('ClassLens_DB')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
app.conf.update(
    broker_url=redis_url,
    result_backend=redis_url,
    broker_connection_retry_on_startup=True,
)