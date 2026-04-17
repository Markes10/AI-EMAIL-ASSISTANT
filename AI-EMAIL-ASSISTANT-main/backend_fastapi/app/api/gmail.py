from fastapi import APIRouter, Request, HTTPException
from starlette.responses import RedirectResponse
import urllib.parse
from app.config import settings
from app.core.db import get_db
from app.core.jwt import decode_token
from typing import Optional

router = APIRouter()


@router.get('/start')
async def gmail_start(request: Request):
    # Create Google OAuth2 authorization URL. If Authorization header present, include user id in state.
    auth_header = request.headers.get('authorization')
    user_id = None
    if auth_header and auth_header.lower().startswith('bearer '):
        token = auth_header.split(' ', 1)[1]
        try:
            payload = decode_token(token)
            user_id = payload.get('sub')
        except Exception:
            user_id = None

    try:
        from google_auth_oauthlib.flow import Flow
        client_config = {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        }
        flow = Flow.from_client_config(client_config, scopes=[
            'https://www.googleapis.com/auth/gmail.send', 'openid', 'email', 'profile'
        ], redirect_uri=settings.OAUTH_REDIRECT_URI)

        auth_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true', prompt='consent', state=user_id or '')
        return {'auth_url': auth_url, 'state': state}
    except Exception as e:
        raise HTTPException(status_code=500, detail='Failed to build OAuth URL')


@router.get('/callback')
async def gmail_callback(request: Request):
    # Google will redirect here with code and state
    try:
        from google_auth_oauthlib.flow import Flow
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        client_config = {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        }

        # Use same scopes as the start flow so we can retrieve profile/email info
        flow = Flow.from_client_config(client_config, scopes=['https://www.googleapis.com/auth/gmail.send', 'openid', 'email', 'profile'], redirect_uri=settings.OAUTH_REDIRECT_URI)
        # Build full authorization response URL
        auth_resp = str(request.url)
        flow.fetch_token(authorization_response=auth_resp)
        creds = flow.credentials

        # Persist tokens in MongoDB and fetch basic user info
        db = get_db()
        user_id = flow.state or None
        email_address = None
        full_name = None
        try:
            oauth2 = build('oauth2', 'v2', credentials=creds)
            userinfo = oauth2.userinfo().get().execute()
            email_address = userinfo.get('email')
            full_name = userinfo.get('name')
        except Exception:
            email_address = None
            full_name = None

        token_doc = {
            'provider': 'gmail',
            'user_id': user_id,
            'token': creds.token,
            'refresh_token': getattr(creds, 'refresh_token', None),
            'scopes': getattr(creds, 'scopes', None),
            'expiry': creds.expiry.isoformat() if getattr(creds, 'expiry', None) else None,
            'email': email_address,
            'name': full_name
        }
        await db.get_collection('oauth_tokens').update_one({'provider': 'gmail', 'user_id': user_id}, {'$set': token_doc}, upsert=True)

        # Redirect back to frontend OAuth callback page with status and email
        frontend_redirect = settings.FRONTEND_OAUTH_REDIRECT_URI
        params = {
            'status': 'success',
            'user_id': user_id or '',
            'email': email_address or ''
        }
        sep = '&' if '?' in frontend_redirect else '?'
        redirect_url = frontend_redirect + sep + urllib.parse.urlencode(params)
        return RedirectResponse(url=redirect_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail='OAuth callback failed')


@router.get('/status')
async def gmail_status(request: Request):
    # Return whether current authenticated user has a connected Gmail account
    auth_header = request.headers.get('authorization')
    user_id = None
    if auth_header and auth_header.lower().startswith('bearer '):
        token = auth_header.split(' ', 1)[1]
        try:
            payload = decode_token(token)
            user_id = payload.get('sub')
        except Exception:
            user_id = None

    db = get_db()
    token_doc = await db.get_collection('oauth_tokens').find_one({'provider': 'gmail', 'user_id': user_id})
    if not token_doc:
        return {'connected': False}
    return {'connected': True, 'email': token_doc.get('email'), 'name': token_doc.get('name')}


@router.post('/disconnect')
async def gmail_disconnect(request: Request):
    auth_header = request.headers.get('authorization')
    user_id = None
    if auth_header and auth_header.lower().startswith('bearer '):
        token = auth_header.split(' ', 1)[1]
        try:
            payload = decode_token(token)
            user_id = payload.get('sub')
        except Exception:
            user_id = None

    db = get_db()
    await db.get_collection('oauth_tokens').delete_one({'provider': 'gmail', 'user_id': user_id})
    return {'disconnected': True}


@router.post('/send')
async def send_via_gmail(payload: dict, request: Request):
    # payload expected: to, subject, body
    to = payload.get('to')
    subject = payload.get('subject')
    body = payload.get('body')
    if not to or not subject or not body:
        raise HTTPException(status_code=400, detail='to, subject, body are required')

    # identify user
    auth_header = request.headers.get('authorization')
    user_id = None
    if auth_header and auth_header.lower().startswith('bearer '):
        token = auth_header.split(' ', 1)[1]
        try:
            payload_j = decode_token(token)
            user_id = payload_j.get('sub')
        except Exception:
            user_id = None

    db = get_db()
    token_doc = await db.get_collection('oauth_tokens').find_one({'provider': 'gmail', 'user_id': user_id})
    if not token_doc:
        raise HTTPException(status_code=404, detail='No Gmail OAuth tokens found for user')

    try:
        # Prepare credentials and refresh if needed
        from app.core.gmail_utils import prepare_credentials_and_maybe_refresh, send_via_gmail

        creds, _ = await prepare_credentials_and_maybe_refresh(get_db(), user_id)
        if not creds:
            raise HTTPException(status_code=404, detail='No Gmail OAuth tokens found for user')

        # Attempt send (handles attachments if present)
        send_result = await send_via_gmail(creds, to, subject, body, attachments=None)
        return {'sent': True, 'result': send_result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail='Failed to send via Gmail')
