from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from pathlib import Path
from app.config import settings
import aiofiles
from starlette.concurrency import run_in_threadpool
from app.core.db import get_db
from bson.objectid import ObjectId
import os
import traceback

router = APIRouter()

Path(settings.UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)


async def _extract_text_from_file(path: str) -> str:
    # Lightweight extraction for pdf/docx/txt
    ext = path.rsplit('.', 1)[-1].lower()
    try:
        if ext == 'pdf':
            from PyPDF2 import PdfReader
            reader = PdfReader(path)
            pages = [p.extract_text() or "" for p in reader.pages]
            return "\n".join(pages)
        elif ext in ('doc', 'docx'):
            import docx
            doc = docx.Document(path)
            return "\n".join(p.text for p in doc.paragraphs)
        else:
            async with aiofiles.open(path, 'r', encoding='utf-8', errors='ignore') as f:
                return await f.read()
    except Exception:
        return ""


@router.post('/upload')
async def upload_resume(file: UploadFile = File(...), request: Request = None):
    dest = Path(settings.UPLOAD_FOLDER) / file.filename
    content = await file.read()
    async with aiofiles.open(dest, 'wb') as out:
        await out.write(content)

    # optionally upload to S3 and return storage path
    from app.core.storage import upload_file_path
    storage_path = await upload_file_path(str(dest), key=file.filename)

    text = await run_in_threadpool(lambda: _extract_text_from_file(str(dest)))
    import time
    db = get_db()
    resumes = db.get_collection('resumes')
    r = await resumes.insert_one({'filename': file.filename, 'storage_path': storage_path, 'text': text, 'created_at': int(time.time())})
    return {'resume_id': str(r.inserted_id), 'text_excerpt': (text or '')[:400], 'storage_path': storage_path}


@router.post('/match')
async def match_resume(payload: dict):
    job_description = payload.get('jobDescription') or payload.get('job_description')
    resume_id = payload.get('resumeId') or payload.get('resume_id')
    if not job_description:
        raise HTTPException(status_code=400, detail='jobDescription is required')

    db = get_db()
    resumes = db.get_collection('resumes')
    resume_doc = None
    if resume_id:
        try:
            resume_doc = await resumes.find_one({'_id': ObjectId(resume_id)})
        except Exception:
            resume_doc = None
    else:
        resume_doc = await resumes.find_one(sort=[('created_at', -1)])

    if not resume_doc:
        raise HTTPException(status_code=404, detail='Resume not found')

    resume_text = resume_doc.get('text', '')

    # compute match using existing service
    import sys
    from pathlib import Path as P
    base = P(__file__).resolve().parents[3] / 'backend'
    sys.path.insert(0, str(base))
    from services.resume_matcher import compute_match_score

    overall_score, detailed_scores = await run_in_threadpool(lambda: compute_match_score(resume_text or '', job_description))
    # update resume record
    try:
        await resumes.update_one({'_id': resume_doc['_id']}, {'$set': {'matched_score': int(overall_score)}})
    except Exception:
        pass

    return {'match_score': int(overall_score), 'detailed_scores': detailed_scores}


@router.get('/list')
async def list_resumes():
    db = get_db()
    resumes = db.get_collection('resumes')
    docs = []
    async for r in resumes.find().sort('created_at', -1):
        docs.append({'id': str(r.get('_id')), 'filename': r.get('filename'), 'created_at': r.get('created_at'), 'matched_score': r.get('matched_score')})
    return docs
