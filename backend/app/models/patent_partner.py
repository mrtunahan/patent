from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.patent import Patent


class PatentPartner(Base):
    __tablename__ = "patent_partners"
    __table_args__ = {"sqlite_autoincrement": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patent_id: Mapped[int] = mapped_column(
        ForeignKey("patents.id", ondelete="CASCADE"), nullable=False
    )
    partner_name: Mapped[str] = mapped_column(String(200), nullable=False)

    patent: Mapped[Patent] = relationship(back_populates="partners")
