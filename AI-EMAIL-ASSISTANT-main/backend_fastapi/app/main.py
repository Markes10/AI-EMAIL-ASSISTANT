import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

# make existing backend services importable by inserting its path
BASE = Path(__file__).resolve().parents[2]
backend_path = BASE / '..' / 'backend'
sys.path.insert(0, str(backend_path.resolve()))

def create_app() -> FastAPI:
    app = FastAPI(title=settings.APP_NAME)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # include routers
    from app.api import auth, email, tone, reply, resume, summarize, score, preferences, gmail

    app.include_router(auth.router, prefix='/api/auth')
    app.include_router(email.router, prefix='/api/email')
    app.include_router(tone.router, prefix='/api/tone')
    app.include_router(reply.router, prefix='/api/reply')
    app.include_router(resume.router, prefix='/api/resume')
    app.include_router(summarize.router, prefix='/api/summarize')
    app.include_router(score.router, prefix='/api/score')
    app.include_router(preferences.router, prefix='/api/preferences')
    app.include_router(gmail.router, prefix='/api/gmail')
    # intent routes
    from app.api import intent
    app.include_router(intent.router, prefix='/api/intent')

    @app.on_event('startup')
    async def startup():
        # ensure upload folder
        from app.config import settings as _s
        Path(_s.UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)
        # ensure model dir exists
        Path(_s.MODEL_DIR).mkdir(parents=True, exist_ok=True)
        # attempt to load persisted intent classifier if present
        try:
            import joblib
            from pathlib import Path as _P
            MODEL_PATH = Path(_s.MODEL_DIR) / 'intent_model.joblib'
            if MODEL_PATH.exists():
                data = joblib.load(MODEL_PATH)
                import importlib, sys
                base = Path(__file__).resolve().parents[2] / '..' / 'backend'
                sys.path.insert(0, str(base))
                ic = importlib.import_module('services.intent_classifier')
                setattr(ic, '_MODEL', data.get('model'))
                setattr(ic, '_LE', data.get('le'))
        except Exception:
            pass

    return app


app = create_app()
