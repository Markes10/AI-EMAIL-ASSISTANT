from celery import Celery
from app.config import settings

# Use configured Redis URL for Celery broker/backend
broker = settings.REDIS_URL
celery_app = Celery('worker', broker=broker, backend=broker)


@celery_app.task
def send_email_task(subject, body, to, attachments=None):
    import sys
    from pathlib import Path
    base = Path(__file__).resolve().parents[3] / 'backend'
    sys.path.insert(0, str(base))
    from services.sender import send_email as ssend
    ssend(subject=subject, body=body, to=to, attachments=attachments or [])
