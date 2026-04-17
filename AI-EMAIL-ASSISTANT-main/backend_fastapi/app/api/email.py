from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, Request, Form
from typing import List
from app.schemas.email import EmailGenerateRequest
from app.core.db import get_db
from starlette.concurrency import run_in_threadpool
from app.config import settings
from app.core.rate_limiter import ensure_allowed_or_429
from app.core.jwt import decode_token
import os
from pathlib import Path
import aiofiles
from bson.objectid import ObjectId

router = APIRouter()

# ensure uploads folder
Path(settings.UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)


@router.post('/generate')
async def generate_email(req: EmailGenerateRequest, request: Request = None):
    # rate limit by client IP
    client_ip = None
    try:
        client_ip = request.client.host if request and request.client else None
    except Exception:
        client_ip = None
    await ensure_allowed_or_429('generate_email', limit=8, period=60, identifier=client_ip)
    # call existing generator in a threadpool
    import sys
    from pathlib import Path
    base = Path(__file__).resolve().parents[3] / 'backend'
    sys.path.insert(0, str(base))
    from services.generator import generate_email as gen
    # Call generator with correct argument order: subject, context, tone, recipient_name
    body = await run_in_threadpool(lambda: gen(req.subject, req.context, req.tone, req.recipient_name, req.use_gpt))
    db = get_db()
    emails = db.get_collection('emails')
    doc = {
        'subject': req.subject,
        'body': body,
        'tone': req.tone,
        'recipient': req.recipient,
        'cc': req.cc,
        'bcc': req.bcc,
    }
    r = await emails.insert_one(doc)
    return {'id': str(r.inserted_id), 'subject': req.subject, 'body': body}


@router.post('/send')
async def send_email(
    background_tasks: BackgroundTasks,
    subject: str = Form(...),
    body: str = Form(...),
    recipient: str = Form(...),
    send_via_gmail: bool = Form(False),
    attachments: List[UploadFile] = File(None),
    request: Request = None
):
    # save files temporarily
    saved_paths = []
    for f in attachments or []:
        dest = Path(settings.UPLOAD_FOLDER) / f.filename
        async with aiofiles.open(dest, 'wb') as out:
            content = await f.read()
            await out.write(content)
        saved_paths.append(str(dest))

    db = get_db()
    emails = db.get_collection('emails')

    # If send_via_gmail requested, try to enqueue a Gmail send using stored OAuth tokens
    if send_via_gmail:
        # identify user
        auth_header = request.headers.get('authorization') if request else None
        user_id = None
        if auth_header and auth_header.lower().startswith('bearer '):
            token = auth_header.split(' ', 1)[1]
            try:
                payload_j = decode_token(token)
                user_id = payload_j.get('sub')
            except Exception:
                user_id = None

        token_doc = await db.get_collection('oauth_tokens').find_one({'provider': 'gmail', 'user_id': user_id})
        if not token_doc:
            # Fall back to local sender but inform client
            def _send_fallback():
                import sys
                from pathlib import Path
                base = Path(__file__).resolve().parents[3] / 'backend'
                sys.path.insert(0, str(base))
                from services.sender import send_email as ssend
                ssend(subject=subject, body=body, to=recipient, attachments=saved_paths)

            background_tasks.add_task(_send_fallback)
            r = await emails.insert_one({'subject': subject, 'body': body, 'recipient': recipient, 'sent_via': 'local_fallback'})
            return {'message': 'No Gmail tokens for user; queued local send', 'id': str(r.inserted_id)}

        # Enqueue Gmail send in background (supports attachments)
        def _send_gmail():
            try:
                # Use synchronous pymongo + google auth flow in background to avoid async loop issues
                from pymongo import MongoClient
                from google.oauth2.credentials import Credentials
                from google.auth.transport.requests import Request
                from googleapiclient.discovery import build
                import base64
                from email.mime.text import MIMEText
                from email.mime.base import MIMEBase
                from email.mime.multipart import MIMEMultipart
                from email import encoders

                client = MongoClient(settings.MONGO_URI)
                db_sync = client[settings.MONGO_DB]
                token_doc_sync = db_sync.get_collection('oauth_tokens').find_one({'provider': 'gmail', 'user_id': user_id})
                if not token_doc_sync:
                    raise Exception('no tokens')

                creds = Credentials(
                    token_doc_sync.get('token'),
                    refresh_token=token_doc_sync.get('refresh_token'),
                    client_id=settings.GOOGLE_CLIENT_ID,
                    client_secret=settings.GOOGLE_CLIENT_SECRET,
                    token_uri='https://oauth2.googleapis.com/token'
                )

                try:
                    if not creds.valid and creds.refresh_token:
                        creds.refresh(Request())
                        # persist refreshed token
                        upd = {}
                        if getattr(creds, 'token', None):
                            upd['token'] = creds.token
                        if getattr(creds, 'refresh_token', None):
                            upd['refresh_token'] = creds.refresh_token
                        if getattr(creds, 'expiry', None):
                            try:
                                upd['expiry'] = creds.expiry.isoformat()
                            except Exception:
                                pass
                        if upd:
                            db_sync.get_collection('oauth_tokens').update_one({'provider': 'gmail', 'user_id': user_id}, {'$set': upd}, upsert=True)
                except Exception:
                    # refresh failed; we'll attempt to continue and fall back if necessary
                    pass

                service = build('gmail', 'v1', credentials=creds)

                if saved_paths:
                    message = MIMEMultipart()
                    message['to'] = recipient
                    message['subject'] = subject
                    message.attach(MIMEText(body))
                    for p in saved_paths:
                        try:
                            with open(p, 'rb') as f:
                                part = MIMEBase('application', 'octet-stream')
                                part.set_payload(f.read())
                            encoders.encode_base64(part)
                            part.add_header('Content-Disposition', 'attachment', filename=Path(p).name)
                            message.attach(part)
                        except Exception:
                            continue
                    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
                else:
                    msg = MIMEText(body)
                    msg['to'] = recipient
                    msg['subject'] = subject
                    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

                try:
                    service.users().messages().send(userId='me', body={'raw': raw}).execute()
                    return
                except Exception:
                    # Gmail send failed - fall through to local fallback
                    pass

                # Fallback to local sender
                import sys
                from pathlib import Path as _P
                base = Path(__file__).resolve().parents[3] / 'backend'
                sys.path.insert(0, str(base))
                from services.sender import send_email as ssend
                ssend(subject=subject, body=body, to=recipient, attachments=saved_paths)

            except Exception:
                # On failure, fall back to local sender
                import sys
                from pathlib import Path as _P
                base = Path(__file__).resolve().parents[3] / 'backend'
                sys.path.insert(0, str(base))
                from services.sender import send_email as ssend
                ssend(subject=subject, body=body, to=recipient, attachments=saved_paths)

        background_tasks.add_task(_send_gmail)
        r = await emails.insert_one({'subject': subject, 'body': body, 'recipient': recipient, 'sent_via': 'gmail'})
        return {'message': 'Queued for send via Gmail', 'id': str(r.inserted_id)}

    # Default: local sender
    def _send_local():
        import sys
        from pathlib import Path
        base = Path(__file__).resolve().parents[3] / 'backend'
        sys.path.insert(0, str(base))
        from services.sender import send_email as ssend
        ssend(subject=subject, body=body, to=recipient, attachments=saved_paths)

    background_tasks.add_task(_send_local)
    r = await emails.insert_one({'subject': subject, 'body': body, 'recipient': recipient, 'sent_via': 'local'})
    return {'message': 'Queued for send', 'id': str(r.inserted_id)}
