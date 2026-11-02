from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.utils import utc_now
from app.database import Base
from app.models.applicant import Applicant
from app.models.attorney_firm import AttorneyFirm
from app.models.department import Department
from app.models.fsmh_type import FsmhType
from app.models.patent_partner import PatentPartner


class Patent(Base):
    __tablename__ = "patents"
    __table_args__ = {"sqlite_autoincrement": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    applicant_id: Mapped[int] = mapped_column(
        ForeignKey("applicants.id"), nullable=False, index=True
    )
    department_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.id"), nullable=True
    )
    fsmh_type_id: Mapped[int] = mapped_column(
        ForeignKey("fsmh_types.id"), nullable=False, index=True
    )
    attorney_firm_id: Mapped[int | None] = mapped_column(
        ForeignKey("attorney_firms.id"), nullable=True
    )
    application_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    registration_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now, nullable=False
    )

    applicant: Mapped[Applicant] = relationship()
    department: Mapped[Department | None] = relationship()
    fsmh_type: Mapped[FsmhType] = relationship()
    attorney_firm: Mapped[AttorneyFirm | None] = relationship()
    partners: Mapped[list[PatentPartner]] = relationship(
        back_populates="patent", cascade="all, delete-orphan", passive_deletes=True,
        order_by="PatentPartner.id",
    )
