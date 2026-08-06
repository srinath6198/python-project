from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    # `users` already belongs to the pre-existing billing schema.  Keep this
    # FastAPI authentication module separate so it cannot alter legacy users.
    __tablename__ = "app_users"

    # The existing MySQL column is named `id`; expose it as `userid` in Python
    # and API responses without requiring a database column rename.
    userid: Mapped[int] = mapped_column("id", Integer, primary_key=True, index=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    role: Mapped[str] = mapped_column(String(50), default="user", index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
