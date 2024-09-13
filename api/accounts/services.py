import jwt
from datetime import timedelta, timezone, datetime
from typing import Annotated
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import exists
from psycopg2.errors import UniqueViolation

import config
from .models import User, RefreshToken
from .schemas import UserInDB, UserLogin, UserRegister, UserRefreshTokenData, UserBase


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

    def check_user_tokens(self, user):
        if len(user.tokens) > 0:
            return True
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Credentials error: Token expired.'
                                )
    
    def check_refresh_expired(self, db: Session, token: str):
        token_in_db = db.query(RefreshToken).filter(RefreshToken.token == token).first()
        if token_in_db:
            if token_in_db.expires_at.tzinfo is None:
                token_in_db.expires_at = token_in_db.expires_at.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) > token_in_db.expires_at:
                db.delete(token_in_db)
                db.commit()
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail='Credentials error: Token expired.')
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Credentials error: Token expired.')
    
    def encode_data(self, data: dict, token_type: str) -> str:
        expire = datetime.now(timezone.utc) + (
            timedelta(minutes=config.ACCESS_TOKEN_EXPIRES_MINUTES) 
            if token_type == 'access' else 
            timedelta(days=config.REFRESH_TOKEN_EXPIRES_DAYS)
        )
        
        to_encode = {'exp': expire, **data}  # Access токен будет содержать только необходимую информацию
        encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
        return encoded_jwt

    def create_refresh_token(self, db: Session, data: UserRefreshTokenData) -> RefreshToken:
        user = self.get_user(db, username=data.username)
        if not user:
            raise ValueError("User not found.")
        
        token_data = {'sub': user.id}
        token = self.encode_data(token_data, token_type='refresh')
        
        db_token = RefreshToken(user=user, user_id=user.id, token=token)
        db.add(db_token)
        db.commit()
        return db_token

    def create_access_token(self, db: Session, refresh_token: str) -> str:
        try:
            data = jwt.decode(refresh_token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
            user_id = data.get('sub')
            if user_id is None:
                raise InvalidTokenError("Credentials error.")
            
            user = db.query(User).get(user_id)
            if not user:
                raise ValueError("User not found.")
            
            access_token_data = {'username': user.username}
            return self.encode_data(access_token_data, token_type='access')

        except InvalidTokenError:
            raise InvalidTokenError("Invalid refresh token.")

    def get_current_user(self, token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(config.get_db)):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
            exp = payload.get('exp')
            exp_datetime = datetime.fromtimestamp(exp, tz=timezone.utc)
            if datetime.now(timezone.utc) > exp_datetime:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail='Credentials error: Token expired.'
                    )
            username = payload.get('username')
            if username is None:
                raise credentials_exception
        except InvalidTokenError:
            raise credentials_exception

        user = self.get_user(db, username=username)
        self.check_user_tokens(user)
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
            refresh_token = self.jwt_service.create_refresh_token(db, data=UserRefreshTokenData(**user.__dict__))
            access_token = self.jwt_service.create_access_token(refresh_token.token)
            print(access_token)
            db.commit()
            return {'refresh': refresh_token.token, 'access': access_token}

        except (IntegrityError, ValueError, InvalidTokenError):
            db.rollback()
            raise 

        except Exception as e:
            db.rollback()
            raise ValueError(f"Unexpected error: {str(e)}")

    def login_user(self, data: UserLogin, db: Session = Depends(config.get_db)):
        password = data.password
        user = self.jwt_service.get_user(db, username=data.username)
        if user:
            if self.jwt_service.verify_password(password, user.hashed_password):
                try:
                    refresh_token = self.jwt_service.create_refresh_token(db, data=user)
                    access_token = self.jwt_service.create_access_token(db, refresh_token.token)
                    db.commit()
                except ValueError:
                    db.rollback()
                    raise
                except Exception as e:
                    print(e)
                return {'refresh': refresh_token.token, 'access': access_token}
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail='Wrong password.'
                    )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f'Account with username {data.username} is not found'
            )
    
    def logout(self, user, db: Session):
        if len(user.tokens) > 0:
            db.delete(user.tokens[0])
            db.commit()
            return {'detail': 'Logged out successfully!'}
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f'Could not validate credentials',
            )
        