import jwt
from datetime import timedelta, timezone, datetime
from typing import Annotated
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from psycopg2.errors import UniqueViolation

import config
from .models import User, RefreshToken
from .schemas import UserInDB, UserRegister, UserRefreshTokenData, UserBase


class JWTService:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

    def get_user(self, db: Session, username: str) -> UserInDB:
        user = db.query(User).filter(User.username == username).first()
        if user:
            return user

    def verify_password(self, raw_password: str, hashed_password: str):
        return self.pwd_context.verify(raw_password, hashed_password)

    def encrypt_password(self, password: str):
        return self.pwd_context.hash(password)

    def encode_data(self, data: dict, token_type: str):
        if token_type:
            if token_type == 'access':
                expire = datetime.now(timezone.utc) + timedelta(
                    minutes=config.ACCESS_TOKEN_EXPIRES_MINUTES)
                to_encode = data.copy()
            elif token_type == 'refresh':
                expire = datetime.now(timezone.utc) + timedelta(
                    days=config.REFRESH_TOKEN_EXPIRES_DAYS)
                to_encode = {'username': data.username, 'email': data.email}

            to_encode.update({'exp': expire})
            encoded_jwt = jwt.encode(to_encode,
                                     config.SECRET_KEY, algorithm=config.ALGORITHM)
            return encoded_jwt

    def create_refresh_token(self, db: Session, data: dict):
        user = self.get_user(db, username=data.username)
        token = self.encode_data(data, token_type='refresh')
        db_token = RefreshToken(user=user, user_id=user.id, token=token)
        db.add(db_token)
        return db_token

    def create_access_token(self, refresh_token: str):
        data = jwt.decode(refresh_token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        if data.get('username'):
            token = self.encode_data(data, token_type='access')
            return token

    def get_current_user(self, token: Annotated[str, Depends(oauth2_scheme)],
                         db: Session = Depends(config.get_db)):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
            username = payload.get('username')
            if username is None:
                raise credentials_exception
            token_data = UserBase(username=username)
        except InvalidTokenError:
            raise credentials_exception
        user = self.get_user(db, username=token_data.username)
        if user is None:
            raise credentials_exception
        return user


class UserService:
    def __init__(self):
        self.jwt_service = JWTService()

    def create_user(self, db: Session, user: User):
        try:
            db.add(user)
            db.commit()
            db.refresh(user)
        except IntegrityError as e:
            if isinstance(e.orig, UniqueViolation):
                raise ValueError('Email is already taken')
            else:
                raise ValueError('An error occurred during user creation')
        return UserRefreshTokenData(**user.__dict__)

    def register_user(self, data: UserRegister, db: Session = Depends(config.get_db)):
        hashed_password = self.jwt_service.encrypt_password(data.password)
        user_data = User(
            username=data.username,
            email=data.email,
            hashed_password=hashed_password,
        )

        try:
            user = self.create_user(db, user_data)
            refresh_token = self.jwt_service.create_refresh_token(db, data=user_data)
            access_token = self.jwt_service.create_access_token(db, refresh_token.token, data=user)
            db.commit()
            return {'refresh': refresh_token.token, 'access': access_token}

        except IntegrityError:
            db.rollback()
            raise ValueError("An error occurred during registration.")

        except ValueError:
            raise

        except Exception as e:
            db.rollback()
            raise ValueError(f"Unexpected error: {str(e)}")
