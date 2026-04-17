from fastapi import APIRouter, Request
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool
from app.core.cache import cache_get, cache_set
from app.core.rate_limiter import ensure_allowed_or_429
import hashlib

router = APIRouter()


class SummarizeRequest(BaseModel):
    text: str
    max_length: int = 120


@router.post('/')
async def summarize(req: SummarizeRequest, request: Request = None):
    # rate limit per IP
    client_ip = None
    try:
        client_ip = request.client.host if request and request.client else None
    except Exception:
        client_ip = None
    await ensure_allowed_or_429('summarize', limit=15, period=60, identifier=client_ip)

    # cache key
    key_raw = f"summ:{hashlib.sha256((req.text + str(req.max_length)).encode('utf-8')).hexdigest()}"
    cached = await cache_get(key_raw)
    if cached:
        return {'summary': cached, 'action_item_count': 0, 'cached': True}

    # Use transformers summarization pipeline in threadpool
    def _run():
        try:
            from transformers import pipeline
            summarizer = pipeline('summarization')
            out = summarizer(req.text, max_length=req.max_length, min_length=30, do_sample=False)
            summary = out[0]['summary_text']
        except Exception:
            # fallback: naive first-3-sentences
            import re
            sents = re.split(r'(?<=[.!?]) +', req.text)
            summary = ' '.join(sents[:3])
        # simple action item extraction
        import re
        actions = re.findall(r"(?:please|action|follow up|due).*?([\.|!|?])", req.text, flags=re.I)
        return {'summary': summary, 'action_item_count': len(actions)}

    result = await run_in_threadpool(_run)
    try:
        # cache summary text only
        await cache_set(key_raw, result['summary'], expire=300)
    except Exception:
        pass
    result['cached'] = False
    return result
