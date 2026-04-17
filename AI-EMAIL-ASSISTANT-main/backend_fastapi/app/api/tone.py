from fastapi import APIRouter, HTTPException, Request
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel
from app.core.rate_limiter import ensure_allowed_or_429

router = APIRouter()


class ToneRequest(BaseModel):
    text: str
    target_tone: str = 'Formal'


@router.post('/adjust')
async def adjust_tone(req: ToneRequest, request: Request = None):
    # rate limit per IP
    client_ip = None
    try:
        client_ip = request.client.host if request and request.client else None
    except Exception:
        client_ip = None
    await ensure_allowed_or_429('tone_adjust', limit=12, period=60, identifier=client_ip)

    import sys
    from pathlib import Path
    base = Path(__file__).resolve().parents[3] / 'backend'
    sys.path.insert(0, str(base))
    from services.tone_adapter import adjust_tone as adjust

    new_text = await run_in_threadpool(lambda: adjust(req.text, target_tone=req.target_tone))
    return {'adjusted': new_text}
