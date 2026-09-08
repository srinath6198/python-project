
from datetime import datetime
from pydantic import BaseModel, Field


class ConfigCreate(BaseModel):
    config_type: str = Field(..., min_length=2, max_length=50)
    config_name: str = Field(..., min_length=1, max_length=100)
    is_active: bool = True


class ConfigUpdate(BaseModel):
    config_type: str = Field(..., min_length=2, max_length=50)
    config_name: str = Field(..., min_length=1, max_length=100)
    is_active: bool = True


class ConfigOut(BaseModel):
    config_id: int
    company_id: int
    config_type: str
    config_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
    