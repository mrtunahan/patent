from datetime import date
from typing import Annotated, Literal

from pydantic import BeforeValidator, Field, model_validator

from app.schemas.common import (
    ForeignId,
    InSchema,
    OptionalText,
    Page,
    ReadSchema,
    RequiredStr200,
    RequiredStr500,
    UtcDatetime,
    strip_or_none,
)


class PatentIn(InSchema):
    title: RequiredStr500
    applicant_id: ForeignId
    fsmh_type_id: ForeignId
    department_id: ForeignId | None = None
    attorney_firm_id: ForeignId | None = None
    application_date: date | None = None  # boş ve gelecek tarih geçerli (Madde 6/3)
    notes: OptionalText = None
    # Normalize edilmiş tekrar kontrolü servis katmanında yapılacak.
    partners: list[RequiredStr200] = Field(default_factory=list)


class ApplicantRef(ReadSchema):
    id: int
    full_name: str


class NamedRef(ReadSchema):
    id: int
    name: str


def _partner_names(value):
    """ORM PatentPartner nesnelerini ad listesine çevirir; str listesi aynen geçer."""
    if isinstance(value, (list, tuple)):
        return [getattr(p, "partner_name", p) for p in value]
    return value


class PatentRead(ReadSchema):
    id: int
    title: str
    applicant: ApplicantRef
    department: NamedRef | None
    fsmh_type: NamedRef
    attorney_firm: NamedRef | None
    partners: Annotated[list[str], BeforeValidator(_partner_names)]
    application_date: date | None
    notes: str | None
    created_at: UtcDatetime
    updated_at: UtcDatetime


SortBy = Literal[
    "id", "title", "applicant", "department", "fsmh_type",
    "attorney_firm", "application_date", "created_at",
]


class PatentListQuery(InSchema):
    q: Annotated[str | None, BeforeValidator(strip_or_none)] = None
    applicant_id: int | None = None
    department_id: int | None = None
    fsmh_type_id: int | None = None
    attorney_firm_id: int | None = None
    date_from: date | None = None
    date_to: date | None = None
    has_attorney: bool | None = None
    sort_by: SortBy = "id"
    sort_dir: Literal["asc", "desc"] = "asc"
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=25, ge=1, le=100)

    @model_validator(mode="after")
    def _check_date_range(self):
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("date_from, date_to'dan büyük olamaz")
        return self


PatentListResponse = Page[PatentRead]
