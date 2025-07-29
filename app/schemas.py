from pydantic import BaseModel

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    username: str | None = None
    password: str | None = None

class User(UserBase):
    id: int

    class Config:
        orm_mode = True
