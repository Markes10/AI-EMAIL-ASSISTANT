from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.db import get_db

router = APIRouter()


class PrefsIn(BaseModel):
    user_id: str
    preferred_tone: str = 'Formal'
    language: str = 'en'


@router.post('/')
async def set_prefs(p: PrefsIn):
    db = get_db()
    prefs = db.get_collection('preferences')
    await prefs.update_one({'user_id': p.user_id}, {'$set': p.dict()}, upsert=True)
    return {'message': 'Saved'}


@router.get('/{user_id}')
async def get_prefs(user_id: str):
    db = get_db()
    prefs = db.get_collection('preferences')
    doc = await prefs.find_one({'user_id': user_id})
    if not doc:
        raise HTTPException(status_code=404, detail='Not found')
    doc['id'] = str(doc['_id'])
    return doc
