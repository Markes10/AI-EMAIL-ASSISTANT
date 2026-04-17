from pathlib import Path
from starlette.concurrency import run_in_threadpool
from app.config import settings


def _make_backend_path():
    # path to the original Flask backend services
    base = Path(__file__).resolve().parents[2] / '..' / 'backend'
    return str(base.resolve())


def generate_email(subject: str, context: str, tone: str = 'Formal', recipient_name: str = None, use_gpt: bool = True):
    import sys
    sys.path.insert(0, _make_backend_path())
    from services.generator import generate_email as gen
    return gen(subject, context, tone, recipient_name, use_gpt)


def summarize_text(text: str, max_length: int = 120):
    try:
        from transformers import pipeline
        summarizer = pipeline('summarization')
        out = summarizer(text, max_length=max_length, min_length=30, do_sample=False)
        return out[0]['summary_text']
    except Exception:
        # naive fallback
        import re
        sents = re.split(r'(?<=[.!?]) +', text)
        return ' '.join(sents[:3])
