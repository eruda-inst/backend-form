from pydantic import BaseModel, EmailStr
from typing import Optional


class LoginInput(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    id: str
    username: str
    email: str
    firstName: str
    lastName: str
    gender: Optional[str] = None
    image: Optional[str] = None
    accessToken: str
    refreshToken: str

class RefreshRequest(BaseModel):
    refresh_token: str

