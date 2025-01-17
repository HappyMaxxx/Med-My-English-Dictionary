import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mad.settings')

app = Celery('mad')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'top_update': {
        'task': 'med.tasks.update_top',
        'schedule': crontab(minute='*/15'),
    },
}