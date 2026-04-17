Overview

This document maps the High-Level Architecture Diagram and Data Flow to the repository's files and components. It describes where each major component is implemented and how data flows through the system.

Frontend UI (React)
- Files: frontend/src/*
- Key components:
  - `frontend/src/components/EmailForm.jsx`: Compose UI, attachments, resume upload, tone selection, generate/send flows.
  - `frontend/src/components/AuthForm.jsx`: Login/Register flow
  - `frontend/src/components/HistoryViewer.jsx`: Email history + export to PDF
- API client: `frontend/src/utils/api.js` (adds JWT header, provides `auth`, `emails`, `resumes`, `reply`, `tone` helpers)

Backend API (Flask)
- App entry: `backend/main.py` — app factory, blueprint registration, DB init, metrics init
- Auth Controller: `backend/routes/auth.py` — register/login
- Email Controller: `backend/routes/email.py` — generate & send (supports multipart/form-data attachments)
- History Controller: `backend/routes/history.py` — list & export to PDF
- Resume Controller: `backend/routes/resume.py` — upload, match, list resumes (file processing)
- Reply Controller: `backend/routes/reply.py` — reply generation (uses intent classifier + generator)
- Tone Controller: `backend/routes/tone.py` — LLM-backed tone adjustment

AI Engine (Generation)
- Service: `backend/services/generator.py` — orchestrates OpenAI / Hugging Face generation for emails
- Tone helper: `backend/services/tone_adapter.py` — analyze & adjust tone (LLM-backed rewrite)
- Intent classifier: `backend/services/intent_classifier.py` — simple rule-based intent detection
- Resume matcher: `backend/services/resume_matcher.py` — resume <-> job description matching

File Processor
- Resume parsing: `backend/routes/resume.py` (uses `PyPDF2` and `python-docx` best-effort extraction)
- PDF Export: `backend/services/pdf_exporter.py`
- Uploads location: configured via `backend/config.py` `UPLOAD_FOLDER` (defaults to `./uploads`)

Database
- SQLAlchemy models: `backend/models/*.py` — `User`, `EmailRecord`, `Resume`
- DB session helpers: `backend/database/db.py` — engine, Base, `get_db()`, `init_db()`

Security & Auth
- JWT helpers: `backend/utils/jwt.py` (creates tokens compatible with `flask_jwt_extended` when available)
- Encryption & hashing: `backend/utils/encryption.py` (bcrypt + Fernet)
- Validators: `backend/utils/validators.py` (email, password, file validation)

External Services & Integrations
- OpenAI: used by `backend/services/generator.py` and `backend/services/tone_adapter.py` when `OPENAI_API_KEY` is set
- SMTP: `backend/services/sender.py` (EmailSender wrapper with attachment support)

Metrics & Monitoring
- Prometheus metrics: `backend/utils/metrics.py` (counters/gauges)
- Initialized in `backend/main.py` via `init_metrics(app)`

Data Flow (request example: generate email)
1. User enters subject/context/tone in the frontend and clicks "Generate".
2. Frontend calls `POST /api/email/generate` via `emails.generate` in `frontend/src/utils/api.js`.
3. `backend/routes/email.py` receives the request, calls `services/generator.generate_email()`.
4. `services/generator` calls OpenAI (or Hugging Face fallback) to produce body, returns string.
5. Route saves `EmailRecord` in DB and returns `{ subject, body, tone, email_id }`.
6. Frontend displays generated content; user may click "Adjust Tone" which calls `POST /api/tone/adjust`.
7. `backend/routes/tone.py` calls `services/tone_adapter.adjust_tone()` which uses OpenAI ChatCompletion to rewrite the email in the requested tone and returns the adjusted text.

Notes & Next Steps
- For production: secure env secrets, enable proper storage for uploads (S3), add async task queue (Celery + Redis) for heavy tasks (large attachments, long gen), add OAuth2 for Gmail/Outlook integrations.
- Replace rule-based intent classifier with a lightweight ML model for higher accuracy.
- Implement persistent metrics export and dashboards (Grafana) using Prometheus scraping.

This file should help reviewers trace code to the architecture components and understand where to extend functionality.
