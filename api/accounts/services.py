import jwt
from datetime import timedelta, timezone, datetime
from typing import Annotated
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from contextlib import contextmanager

import config
from .models import User, RefreshToken
from .schemas import UserInDB, UserBase, UserDetails

@contextmanager
def get_db():
    db = config.SessionLocal()
    try:
        yield db
    finally:
        db.close()
        


class UserService:
    def create_user(self, db: Session, user: User):
        with get_db() as db:
            db.add(user)
            db.commit()
            db.refresh(user)
        return UserDetails(username=user.username, id=int(user.id))
            
        
        
class JWTService:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
    
    def get_user(self, db: Session, username: str) -> UserInDB:
        user = db.query(User).filter(User.username == username).first()
        if user:
            return UserInDB(**user)
        
    def encode_data(self, data: dict, token_type: str):
        to_encode = data.copy()
        if token_type:
            if token_type == 'access':
                expire = datetime.now(timezone.utc) + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
            elif token_type == 'refresh':
                expire = datetime.now(timezone.utc) + timedelta(days=config.REFRESH_TOKEN_EXPIRES_DAYS)
            
            to_encode.update({'exp': expire})
            encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
            return encoded_jwt
    
    def create_refresh_token(self, db: Session, data: dict):
        user = self.get_user(username=data.get('username'))
        token = self.encode_data(data, token_type='refresh')

        with get_db() as db:
            db_token = RefreshToken(user=user, user_id=user.id, token=token)
            db.add(token)
        
        return db_token.token
    
