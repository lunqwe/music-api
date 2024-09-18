from typing import Annotated
from fastapi import FastAPI, Depends, status, HTTPException
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from config import get_db
from .schemas import UserBase, UserRegister, RefreshToken, UserLogin
from .services import UserService, JWTService
from .models import User

app = FastAPI()
user_service = UserService()
jwt_service = JWTService()


@app.post('/register', tags=['accounts'])
async def register(request: UserRegister, db: Session = Depends(get_db)):
    try:
        data = user_service.register_user(data=request, db=db)
        return JSONResponse(content=data, status_code=status.HTTP_201_CREATED)
    except ValueError as e:
        return HTTPException(status_code=401, details=e.args[0])
    except IntegrityError as e:
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, details=e.args[0])


@app.post('/refresh', tags=['accounts'])
async def refresh_token(request: RefreshToken, db: Session = Depends(get_db)):
    jwt_service.check_refresh_expired(db, request.refresh)
    access_token = jwt_service.create_access_token(db, refresh_token=request.refresh)
    return JSONResponse({'access': access_token}, status_code=status.HTTP_201_CREATED)


@app.post('/login', tags=['accounts'])
async def login(data: UserLogin, db: Session = Depends(get_db)):
    response_data = user_service.login_user(data, db)
    return JSONResponse(response_data, status_code=status.HTTP_200_OK)


@app.post('/logout', tags=['accounts'])
async def logout(current_user: Annotated[User,
                                         Depends(jwt_service.get_current_user)],
                 db: Session = Depends(get_db)):
    response_data = user_service.logout(user=current_user, db=db)
    return JSONResponse(response_data, status_code=status.HTTP_200_OK)


# jwt tokens test
@app.get("/me", response_model=UserBase, tags=['accounts'])
async def read_users_me(
    current_user: Annotated[User, Depends(jwt_service.get_current_user)],
):
    return JSONResponse(UserBase(**current_user.__dict__).__dict__, status_code=status.HTTP_200_OK)
