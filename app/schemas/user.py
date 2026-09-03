from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str | None = None
    company_id: int | None = None
    company_name: str | None = Field(default=None, min_length=2, max_length=150)


class ProfileUpdateRequest(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    mobile_number: str | None = None
    address: str | None = None
    shopName: str | None = None


class AdminUserCreate(BaseModel):
    company_id: int | None = None
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str | None = None
    mobile_number: str | None = None
    address: str | None = None
    shopName: str | None = None
    role: UserRole
    is_active: bool = True


class AdminUserUpdate(BaseModel):
    company_id: int | None = None
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    full_name: str | None = None
    mobile_number: str | None = None
    address: str | None = None
    shopName: str | None = None
    role: UserRole
    is_active: bool = True
    password: str | None = Field(default=None, min_length=6)


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    user_id: int
    company_id: int | None = None
    username: str
    email: EmailStr
    full_name: str | None = None
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

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