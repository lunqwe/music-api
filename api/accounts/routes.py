from typing import Annotated
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from config import get_db
from .schemas import UserBase, UserRegister, RefreshToken
from .services import UserService, JWTService
from .models import User

app = FastAPI()
user_service = UserService()
jwt_service = JWTService()


@app.post('/register')
async def register(request: UserRegister, db: Session = Depends(get_db)):
    try:
        data = user_service.register_user(data=request, db=db)
        return data
    except ValueError as e:
        return {'detail': e.args[0]}


@app.post('/refresh')
async def refresh_token(request: RefreshToken, db: Session = Depends(get_db)):
    access_token = jwt_service.create_access_token(db, refresh_token=request.refresh)
    return {'access': access_token}

# jwt tokens test


@app.get("/me", response_model=UserBase)
async def read_users_me(
    current_user: Annotated[User, Depends(jwt_service.get_current_user)],
):
    return current_user
