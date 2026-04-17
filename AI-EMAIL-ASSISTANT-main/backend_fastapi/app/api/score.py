from fastapi import APIRouter
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

router = APIRouter()


class ScoreRequest(BaseModel):
    subject: str
    body: str


@router.post('/')
async def score_email(req: ScoreRequest):
    def _score():
        score = 100
        text = req.subject + '\n' + req.body
        # basic heuristics
        if len(req.body) < 30:
            score -= 20
        if 'please' in req.body.lower():
            score += 2
        if any(g in req.body.lower() for g in ['regards', 'sincerely', 'best']):
            score += 3

        # sentiment check
        try:
            from transformers import pipeline
            sentiment = pipeline('sentiment-analysis')
            out = sentiment(req.body[:512])
            lab = out[0]['label'].lower()
            if 'negative' in lab:
                score -= 15
        except Exception:
            pass

        # clamp
        score = max(0, min(100, score))
        return {'score': score}

    return await run_in_threadpool(_score)
