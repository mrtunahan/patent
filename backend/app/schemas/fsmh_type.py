from pydantic import Field

from app.schemas.common import InSchema, ReadSchema, RequiredStr100, UtcDatetime

# 32-bit aralık: negatif serbest; SQLite INTEGER (64-bit) taşmasında 500 yerine 422 döner.
SORT_ORDER_MIN = -(2**31)
SORT_ORDER_MAX = 2**31 - 1


class FsmhTypeIn(InSchema):
    name: RequiredStr100
    sort_order: int = Field(default=0, ge=SORT_ORDER_MIN, le=SORT_ORDER_MAX)


class FsmhTypeRead(ReadSchema):
    id: int
    name: str
    sort_order: int
    created_at: UtcDatetime
    updated_at: UtcDatetime
