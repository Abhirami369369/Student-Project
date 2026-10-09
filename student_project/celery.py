import os
 
from celery import Celery
from celery.schedules import crontab
 
 
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "student_project.settings"
)
 
 
app = Celery(
    "student_project"
)
 
 
app.config_from_object(
    "django.conf:settings",
    namespace="CELERY"
)
 
 
app.autodiscover_tasks()
 
 
app.conf.beat_schedule = {
 
 
    # -----------------------------------
    # Create Scheduled Product
    # -----------------------------------
 
    "create-scheduled-product": {
        "task": "students.tasks.create_scheduled_product",
        "schedule": crontab(
            hour=15,
            minute=30
        ),
    },
 
}