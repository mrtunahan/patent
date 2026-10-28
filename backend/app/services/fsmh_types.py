from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError
from app.core.text import turkish_sort_key
from app.models import FsmhType
from app.schemas import FsmhTypeIn
from app.services.common import IN_USE_MESSAGE, commit_or_conflict, name_taken

DUPLICATE_MESSAGE = "Bu adla bir FSMH türü zaten var."


def list_fsmh_types(db: Session) -> list[FsmhType]:
    types = db.scalars(select(FsmhType)).all()
    return sorted(types, key=lambda t: (t.sort_order, turkish_sort_key(t.name), t.id))


def get_fsmh_type(db: Session, fsmh_type_id: int) -> FsmhType:
    fsmh_type = db.get(FsmhType, fsmh_type_id)
    if fsmh_type is None:
        raise NotFoundError("Tür bulunamadı.")
    return fsmh_type


def create_fsmh_type(db: Session, data: FsmhTypeIn) -> FsmhType:
    if name_taken(db, FsmhType, "name", data.name):
        raise ConflictError(DUPLICATE_MESSAGE)
    fsmh_type = FsmhType(name=data.name, sort_order=data.sort_order)
    db.add(fsmh_type)
    commit_or_conflict(db, DUPLICATE_MESSAGE)
    db.refresh(fsmh_type)
    return fsmh_type


def update_fsmh_type(db: Session, fsmh_type_id: int, data: FsmhTypeIn) -> FsmhType:
    fsmh_type = get_fsmh_type(db, fsmh_type_id)
    if name_taken(db, FsmhType, "name", data.name, exclude_id=fsmh_type_id):
        raise ConflictError(DUPLICATE_MESSAGE)
    fsmh_type.name = data.name
    fsmh_type.sort_order = data.sort_order
    commit_or_conflict(db, DUPLICATE_MESSAGE)
    db.refresh(fsmh_type)
    return fsmh_type


def delete_fsmh_type(db: Session, fsmh_type_id: int) -> None:
    fsmh_type = get_fsmh_type(db, fsmh_type_id)
    db.delete(fsmh_type)
    commit_or_conflict(db, IN_USE_MESSAGE)  # bağlı kayıt varsa FK hatası -> 409
