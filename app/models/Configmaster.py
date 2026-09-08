from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CompanyConfig(Base):
    __tablename__ = "company_configs"

    config_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.company_id"),
        nullable=False,
        index=True
    )

    config_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )

    config_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    