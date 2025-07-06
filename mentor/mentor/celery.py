import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mentor.settings")

app = Celery("mentor")
app.config_from_object("django.conf:settings", namespace="CELERY")
print("CELERY_BROKER_URL in celery.py:", app.conf.broker_url)
app.autodiscover_tasks()
