from app.schemas.common import InSchema, ReadSchema, RequiredStr100, UtcDatetime


class FsmhTypeIn(InSchema):
    name: RequiredStr100
    sort_order: int = 0


class FsmhTypeRead(ReadSchema):
    id: int
    name: str
    sort_order: int
    created_at: UtcDatetime
    updated_at: UtcDatetime
