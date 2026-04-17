from fastapi import APIRouter, HTTPException, Depends
from app.schemas.user import UserCreate, Token
from app.core.db import get_db
from app.core.jwt import create_access_token
from passlib.context import CryptContext
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.config import settings
from pydantic import BaseModel
from typing import Dict
import asyncio
from bson.objectid import ObjectId

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter()


async def get_users_collection(db: AsyncIOMotorDatabase):
    return db.get_collection('users')


@router.post('/register', response_model=Dict)
async def register(user: UserCreate):
    db = get_db()
    users = db.get_collection('users')
    existing = await users.find_one({'email': user.email})
    if existing:
        raise HTTPException(status_code=409, detail='Email already exists')

    hashed = pwd_context.hash(user.password)
    doc = {'email': user.email, 'password_hash': hashed}
    r = await users.insert_one(doc)
    return {'message': 'User registered successfully', 'user_id': str(r.inserted_id)}


class LoginIn(BaseModel):
    email: str
    password: str


@router.post('/login', response_model=Token)
async def login(data: LoginIn):
    db = get_db()
    users = db.get_collection('users')
    user = await users.find_one({'email': data.email})
    if not user or not pwd_context.verify(data.password, user.get('password_hash', '')):
        raise HTTPException(status_code=401, detail='Invalid credentials')

    token = create_access_token(str(user['_id']))
    return {'access_token': token, 'token_type': 'bearer'}
