from sqlalchemy.orm import Session
from prometheus_client import Counter, Histogram, Gauge
from models.email import EmailRecord
from models.resume import Resume
from models.user import User
from datetime import datetime, timedelta

# Prometheus metrics
request_count = Counter('http_requests_total', 'Total HTTP requests')
request_latency = Histogram('http_request_duration_seconds', 'HTTP request latency')
active_users = Gauge('active_users_total', 'Number of active users in the last 7 days')
email_generation_count = Counter('email_generation_total', 'Total number of emails generated')
email_send_count = Counter('email_send_total', 'Total number of emails sent')
resume_match_count = Counter('resume_match_total', 'Total number of resume matches performed')

def init_metrics(app):
    """
    Initialize Prometheus metrics for the Flask app
    """
    @app.before_request
    def before_request():
        request_count.inc()

    @app.after_request
    def after_request(response):
        return response

def get_email_count(db: Session, user_id: int = None) -> int:
    """
    Count total emails generated. Optionally filter by user.
    """
    query = db.query(EmailRecord)
    if user_id:
        query = query.filter(EmailRecord.user_id == user_id)
    count = query.count()
    email_generation_count._value.set(count)  # Update Prometheus metric
    return count

def get_average_match_score(db: Session, user_id: int = None) -> float:
    """
    Compute average resume match score. Optionally filter by user.
    """
    query = db.query(Resume).filter(Resume.matched_score.isnot(None))
    if user_id:
        query = query.filter(Resume.user_id == user_id)
    scores = [r.matched_score for r in query.all()]
    resume_match_count._value.set(len(scores))  # Update Prometheus metric
    return round(sum(scores) / len(scores), 2) if scores else 0.0

def get_active_users(db: Session, days: int = 7) -> int:
    """
    Count users who generated emails in the last `days` days.
    """
    cutoff = datetime.utcnow() - timedelta(days=days)
    user_ids = db.query(EmailRecord.user_id).filter(EmailRecord.timestamp >= cutoff).distinct()
    count = user_ids.count()
    active_users.set(count)  # Update Prometheus metric
    return count

def get_user_metrics(db: Session, user_id: int) -> dict:
    """
    Return a summary of metrics for a specific user.
    """
    return {
        "email_count": get_email_count(db, user_id),
        "average_match_score": get_average_match_score(db, user_id)
    }

def get_global_metrics(db: Session) -> dict:
    """
    Return global usage metrics.
    """
    return {
        "total_emails": get_email_count(db),
        "average_match_score": get_average_match_score(db),
        "active_users_last_7_days": get_active_users(db)
    }