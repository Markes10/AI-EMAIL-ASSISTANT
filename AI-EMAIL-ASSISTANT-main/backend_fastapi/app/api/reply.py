from fastapi import APIRouter, Request
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool
from app.core.rate_limiter import ensure_allowed_or_429

router = APIRouter()


class ReplyRequest(BaseModel):
    email_text: str
    style: str = 'formal'  # short, formal, detailed


@router.post('/generate')
async def generate_reply(req: ReplyRequest, request: Request = None):
    # rate limit per IP
    client_ip = None
    try:
        client_ip = request.client.host if request and request.client else None
    except Exception:
        client_ip = None
    await ensure_allowed_or_429('reply_generate', limit=10, period=60, identifier=client_ip)

    import sys
    from pathlib import Path
    base = Path(__file__).resolve().parents[3] / 'backend'
    sys.path.insert(0, str(base))
    from services.intent_classifier import detect_intent
    from services.generator import generate_email as gen

    intent, score = detect_intent(req.email_text)

    # create prompt for reply generator and call generator correctly
    prompt = f"Reply to the following email with a {req.style} style. Original email:\n{req.email_text}"
    body = await run_in_threadpool(lambda: gen('Re:', prompt, 'Formal' if req.style == 'formal' else 'Casual'))
    return {'reply': body, 'intent': intent, 'confidence': score}
