from pydantic import BaseModel


class UserBase(BaseModel):
    username: str


class UserRegister(UserBase):
    email: str
    password: str


class UserLogin(UserBase):
    password: str


class UserRefreshTokenData(UserBase):
    email: str


class UserInDB(UserBase):
    id: int


class RefreshToken(BaseModel):
    refresh: str
