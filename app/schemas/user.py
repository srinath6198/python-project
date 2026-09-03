from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str | None = None


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    full_name: str | None = None
    is_active: bool
    created_at: datetime | None = None

    class Config:
        from_attributes = True  # allows returning SQLAlchemy objects directly


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: str | None = None
    

class RefreshTokenRequest(BaseModel):
    refresh_token: str
    
class LogoutRequest(BaseModel):
    refresh_token: str


class RegisterResponse(BaseModel):
    user: UserOut
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_at: datetime


# Alias for login endpoint (same structure as register)
AuthResponse = RegisterResponse