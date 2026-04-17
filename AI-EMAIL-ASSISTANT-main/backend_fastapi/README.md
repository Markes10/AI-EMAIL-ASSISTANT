# FastAPI Backend (Scaffold)

Quick start for the new FastAPI backend scaffold included in this repo. This is intended as an incremental, backwards-compatible migration: it reuses existing service modules located in `backend/services` when possible.

Prerequisites
- Python 3.10+
- MongoDB running locally or reachable via `MONGO_URI`
- (Optional) Redis for Celery tasks

Install

```bash
python -m venv .venv
source .venv/bin/activate    # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

Environment
- `MONGO_URI` (default: `mongodb://localhost:27017`)
- `MONGO_DB` (default: `ai_email_assistant`)
- `JWT_SECRET` set to a strong secret
- `OPENAI_API_KEY` (optional)

Run (development)

```bash
# from this directory
uvicorn app.main:app --reload --port 8000
```

Notes
- The scaffold imports existing Flask `backend/services` modules at runtime so you can migrate incrementally.
- Celery is scaffolded in `app/tasks.py` but requires a running Redis instance and adjustments to `broker` URL.