from app.schemas.common import InSchema, OptionalText, ReadSchema, RequiredStr200, UtcDatetime


class AttorneyFirmIn(InSchema):
    name: RequiredStr200
    contact_info: OptionalText = None
    is_active: bool = True


class AttorneyFirmRead(ReadSchema):
    id: int
    name: str
    contact_info: str | None
    is_active: bool
    created_at: UtcDatetime
    updated_at: UtcDatetime
