from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError
from app.core.text import turkish_sort_key
from app.models import AttorneyFirm
from app.schemas import AttorneyFirmIn
from app.services.common import IN_USE_MESSAGE, commit_or_conflict, name_taken

DUPLICATE_MESSAGE = "Bu adla bir vekil firma zaten var."


def list_attorney_firms(db: Session) -> list[AttorneyFirm]:
    firms = db.scalars(select(AttorneyFirm)).all()  # aktif ve pasif hepsi
    return sorted(firms, key=lambda f: (turkish_sort_key(f.name), f.id))


def get_attorney_firm(db: Session, firm_id: int) -> AttorneyFirm:
    firm = db.get(AttorneyFirm, firm_id)
    if firm is None:
        raise NotFoundError("Vekil firma bulunamadı.")
    return firm


def create_attorney_firm(db: Session, data: AttorneyFirmIn) -> AttorneyFirm:
    if name_taken(db, AttorneyFirm, "name", data.name):
        raise ConflictError(DUPLICATE_MESSAGE)
    firm = AttorneyFirm(name=data.name, contact_info=data.contact_info, is_active=data.is_active)
    db.add(firm)
    commit_or_conflict(db, DUPLICATE_MESSAGE)
    db.refresh(firm)
    return firm


def update_attorney_firm(db: Session, firm_id: int, data: AttorneyFirmIn) -> AttorneyFirm:
    firm = get_attorney_firm(db, firm_id)
    if name_taken(db, AttorneyFirm, "name", data.name, exclude_id=firm_id):
        raise ConflictError(DUPLICATE_MESSAGE)
    firm.name = data.name
    firm.contact_info = data.contact_info
    firm.is_active = data.is_active
    commit_or_conflict(db, DUPLICATE_MESSAGE)
    db.refresh(firm)
    return firm


def delete_attorney_firm(db: Session, firm_id: int) -> None:
    firm = get_attorney_firm(db, firm_id)
    db.delete(firm)
    commit_or_conflict(db, IN_USE_MESSAGE)  # bağlı kayıt varsa FK hatası -> 409
