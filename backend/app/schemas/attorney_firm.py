from typing import Annotated

from pydantic import BeforeValidator, StringConstraints

from app.schemas.common import (
    InSchema,
    OptionalStr200,
    OptionalText,
    ReadSchema,
    RequiredStr200,
    UtcDatetime,
    strip_or_none,
)

# Biçim kontrolleri (vergi no, e-posta) servis katmanında yapılır: {"detail": "..."} mesajı için.
OptionalStr20 = Annotated[
    Annotated[str, StringConstraints(max_length=20)] | None, BeforeValidator(strip_or_none)
]
OptionalStr300 = Annotated[
    Annotated[str, StringConstraints(max_length=300)] | None, BeforeValidator(strip_or_none)
]


class AttorneyFirmIn(InSchema):
    name: RequiredStr200
    contact_info: OptionalText = None
    tax_no: OptionalStr20 = None
    title: OptionalStr300 = None
    email: OptionalStr200 = None
    is_active: bool = True


class AttorneyFirmRead(ReadSchema):
    id: int
    name: str
    contact_info: str | None
    tax_no: str | None
    title: str | None
    email: str | None
    is_active: bool
    created_at: UtcDatetime
    updated_at: UtcDatetime
