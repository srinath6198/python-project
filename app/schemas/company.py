from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class CompanyCreate(BaseModel):
    company_code: str = Field(..., min_length=2, max_length=50)
    company_name: str = Field(..., min_length=2, max_length=150)
    email: EmailStr | None = None
    phone: str | None = None
    address: str | None = None
    is_active: bool = True


class CompanyUpdate(CompanyCreate):
    pass


class CompanyOut(CompanyCreate):
    company_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True