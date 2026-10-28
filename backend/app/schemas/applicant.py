from app.schemas.common import InSchema, OptionalStr200, ReadSchema, RequiredStr200, UtcDatetime


class ApplicantIn(InSchema):
    full_name: RequiredStr200
    department_id: int | None = None
    email: OptionalStr200 = None
    is_active: bool = True


class ApplicantRead(ReadSchema):
    id: int
    full_name: str
    department_id: int | None
    email: str | None
    is_active: bool
    created_at: UtcDatetime
    updated_at: UtcDatetime
