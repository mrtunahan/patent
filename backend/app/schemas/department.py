from app.schemas.common import InSchema, ReadSchema, RequiredStr200, UtcDatetime


class DepartmentIn(InSchema):
    name: RequiredStr200


class DepartmentRead(ReadSchema):
    id: int
    name: str
    created_at: UtcDatetime
    updated_at: UtcDatetime
