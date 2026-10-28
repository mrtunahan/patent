from datetime import UTC, datetime
from typing import Annotated, Generic, Literal, TypeVar

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    StringConstraints,
)

T = TypeVar("T")


def _as_utc(value: datetime) -> datetime:
    """DB'den gelen naive datetime UTC kabul edilir; tz-aware ise UTC'ye çevrilir."""
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


UtcDatetime = Annotated[datetime, AfterValidator(_as_utc)]


def strip_or_none(value):
    """Kırpar; boşsa None. Str olmayan değer doğrulayıcıya bozulmadan geçer."""
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return value


# İlişkili kayıt id'si (FK): SQLite 64-bit tamsayı sınırını aşan değer 500 yerine 422 olur.
ForeignId = Annotated[int, Field(le=2**63 - 1)]

# Zorunlu metin: kırpılır (iç boşluklara dokunulmaz), boşsa 422.
RequiredStr100 = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
RequiredStr200 = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
RequiredStr500 = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]

# İsteğe bağlı metin: kırpılır, boşsa None.
OptionalStr200 = Annotated[
    Annotated[str, StringConstraints(max_length=200)] | None, BeforeValidator(strip_or_none)
]
OptionalText = Annotated[str | None, BeforeValidator(strip_or_none)]  # DB'de Text: uzunluk sınırı yok


class InSchema(BaseModel):
    """Girdi şemaları: tanımsız alan (id, created_at vb.) 422."""

    model_config = ConfigDict(extra="forbid")


class ReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int


class DuplicateWarning(BaseModel):
    """Madde 6/4: mükerrer uyarısı, 409 ile döner; ?confirm_duplicate=true ile onaylanır."""

    duplicate: Literal[True]
    detail: str
    existing_ids: list[int]


class ErrorResponse(BaseModel):
    detail: str
