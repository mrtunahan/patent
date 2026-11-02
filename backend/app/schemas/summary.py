from datetime import date

from app.schemas.common import ReadSchema


class PatentRef(ReadSchema):
    id: int
    title: str
    fsmh_type_name: str
    status: str | None
    application_date: date | None
    registration_date: date | None


class PartnerSummary(ReadSchema):
    name: str
    patent_count: int
    patents: list[PatentRef]


class LookupSummary(ReadSchema):
    id: int
    name: str
    patent_count: int
    patents: list[PatentRef]


class ApplicantSummary(ReadSchema):
    id: int
    full_name: str
    patent_count: int
    patents: list[PatentRef]
