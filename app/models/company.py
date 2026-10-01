from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Company(Base):
    __tablename__ = "companies"

    company_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_code = Column(String(50), unique=True, nullable=False, index=True)
    company_name = Column(String(150), nullable=False)
    email = Column(String(255), unique=True, nullable=True)
    phone = Column(String(30), nullable=True)
    address = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    users = relationship("User", back_populates="company")