from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict, Field


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str | None = None
    role: str = "Admin"

class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    userid: int
    username: str
    email: EmailStr
    full_name: str | None
    role: str
    is_active: bool


class RegisterResponse(UserOut):
    access_token: str
    token_type: str = "bearer"


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str = "user"


class TokenData(BaseModel):
    username: str | None = None
