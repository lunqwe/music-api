from pydantic import BaseModel


class UserBase(BaseModel):
    username: str

class UserDetails(UserBase):
    id: int

class UserInDB(UserDetails):
    hashed_pwd: str
    

    


