from app.config import settings
from starlette.concurrency import run_in_threadpool
from pathlib import Path
import base64
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email import encoders


async def prepare_credentials_and_maybe_refresh(db, user_id):
    """Return google Credentials object for user and update tokens in DB if refreshed."""
    token_doc = await db.get_collection('oauth_tokens').find_one({'provider': 'gmail', 'user_id': user_id})
    if not token_doc:
        return None, None

    def _build_and_refresh():
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request

        creds = Credentials(
            token_doc.get('token'),
            refresh_token=token_doc.get('refresh_token'),
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            token_uri='https://oauth2.googleapis.com/token',
            scopes=token_doc.get('scopes') or None
        )

        try:
            # refresh synchronously if needed
            if not creds.valid and creds.refresh_token:
                creds.refresh(Request())
        except Exception:
            # let caller handle failures
            pass

        return creds

    creds = await run_in_threadpool(_build_and_refresh)

    # persist updated tokens when they change
    update = {}
    if getattr(creds, 'token', None) and creds.token != token_doc.get('token'):
        update['token'] = creds.token
    if getattr(creds, 'refresh_token', None) and creds.refresh_token != token_doc.get('refresh_token'):
        update['refresh_token'] = creds.refresh_token
    if getattr(creds, 'expiry', None):
        try:
            update['expiry'] = creds.expiry.isoformat()
        except Exception:
            pass

    if update:
        await db.get_collection('oauth_tokens').update_one({'provider': 'gmail', 'user_id': user_id}, {'$set': update}, upsert=True)

    return creds, token_doc


async def send_via_gmail(creds, to, subject, body, attachments=None):
    """Send email via Gmail API using provided Credentials.

    attachments: list of file paths (local) or None
    """
    def _send():
        from googleapiclient.discovery import build

        service = build('gmail', 'v1', credentials=creds)

        if attachments:
            # Build multipart message
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject
            # body
            body_part = MIMEText(body)
            message.attach(body_part)

            for path in attachments:
                p = Path(path)
                try:
                    with open(p, 'rb') as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', 'attachment', filename=p.name)
                    message.attach(part)
                except Exception:
                    # skip unreadable attachment
                    continue

            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        else:
            msg = MIMEText(body)
            msg['to'] = to
            msg['subject'] = subject
            raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

        return service.users().messages().send(userId='me', body={'raw': raw}).execute()

    return await run_in_threadpool(_send)
