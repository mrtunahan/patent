from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.utils import utc_now
from app.database import Base


class AttorneyFirm(Base):
    __tablename__ = "attorney_firms"
    __table_args__ = {"sqlite_autoincrement": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    contact_info: Mapped[str | None] = mapped_column(Text, nullable=True)
    tax_no: Mapped[str | None] = mapped_column(String(20), nullable=True)
    title: Mapped[str | None] = mapped_column(String(300), nullable=True)
    email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now, nullable=False
    )
