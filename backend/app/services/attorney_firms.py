import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError, UnprocessableError
from app.core.text import turkish_sort_key
from app.models import AttorneyFirm, Patent
from app.schemas import AttorneyFirmIn
from app.services.common import commit_or_conflict, delete_lookup, name_taken

DUPLICATE_MESSAGE = "Bu adla bir vekil firma zaten var."
TAX_NO_MESSAGE = "Vergi no 10 veya 11 haneli rakam olmalı."
EMAIL_MESSAGE = "Geçerli bir e-posta adresi girin."


def _check_fields(data: AttorneyFirmIn) -> None:
    if data.tax_no is not None and not re.fullmatch(r"[0-9]{10,11}", data.tax_no):
        raise UnprocessableError(TAX_NO_MESSAGE)
    if data.email is not None:  # basit biçim: tek @, boşluk yok, alan adı nokta içerir ve noktayla başlayıp bitmez
        local, at, domain = data.email.partition("@")
        if not (local and at and "@" not in domain and re.fullmatch(r"\S+", data.email)
                and "." in domain and not domain.startswith(".") and not domain.endswith(".")):
            raise UnprocessableError(EMAIL_MESSAGE)


def list_attorney_firms(db: Session) -> list[AttorneyFirm]:
    firms = db.scalars(select(AttorneyFirm)).all()  # aktif ve pasif hepsi
    return sorted(firms, key=lambda f: (turkish_sort_key(f.name), f.id))


def get_attorney_firm(db: Session, firm_id: int) -> AttorneyFirm:
    firm = db.get(AttorneyFirm, firm_id)
    if firm is None:
        raise NotFoundError("Vekil firma bulunamadı.")
    return firm


def create_attorney_firm(db: Session, data: AttorneyFirmIn) -> AttorneyFirm:
    _check_fields(data)
    if name_taken(db, AttorneyFirm, "name", data.name):
        raise ConflictError(DUPLICATE_MESSAGE)
    firm = AttorneyFirm(
        name=data.name, contact_info=data.contact_info, tax_no=data.tax_no, title=data.title,
        email=data.email, is_active=data.is_active,
    )
    db.add(firm)
    commit_or_conflict(db, DUPLICATE_MESSAGE)
    db.refresh(firm)
    return firm


def update_attorney_firm(db: Session, firm_id: int, data: AttorneyFirmIn) -> AttorneyFirm:
    firm = get_attorney_firm(db, firm_id)
    _check_fields(data)
    if name_taken(db, AttorneyFirm, "name", data.name, exclude_id=firm_id):
        raise ConflictError(DUPLICATE_MESSAGE)
    firm.name = data.name
    firm.contact_info = data.contact_info
    firm.tax_no = data.tax_no
    firm.title = data.title
    firm.email = data.email
    firm.is_active = data.is_active
    commit_or_conflict(db, DUPLICATE_MESSAGE)
    db.refresh(firm)
    return firm


def delete_attorney_firm(db: Session, firm_id: int) -> None:
    firm = get_attorney_firm(db, firm_id)
    delete_lookup(db, firm, Patent.attorney_firm_id)
