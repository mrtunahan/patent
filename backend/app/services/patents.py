from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import DuplicateWarningError, NotFoundError, UnprocessableError
from app.core.text import normalize_tr
from app.core.utils import utc_now
from app.models import Applicant, AttorneyFirm, Department, FsmhType, Patent, PatentPartner
from app.schemas import PatentIn
from app.services.common import commit_or_conflict

SAVE_ERROR_MESSAGE = "Kayıt kaydedilemedi: ilişkili kayıt değişmiş olabilir."
DUPLICATE_MESSAGE = "Aynı başlık, başvuru sahibi ve tarihle kayıt var."


def get_patent(db: Session, patent_id: int) -> Patent:
    """Yalnızca aktif (deleted_at IS NULL) patent; silinmiş olan 404'tür."""
    patent = db.scalar(select(Patent).where(Patent.id == patent_id, Patent.deleted_at.is_(None)))
    if patent is None:
        raise NotFoundError("Patent bulunamadı.")
    return patent


def _check_references(db: Session, data: PatentIn) -> None:
    checks = [
        (Applicant, data.applicant_id, "Başvuru sahibi", "applicant_id"),
        (FsmhType, data.fsmh_type_id, "FSMH türü", "fsmh_type_id"),
        (Department, data.department_id, "Bölüm", "department_id"),
        (AttorneyFirm, data.attorney_firm_id, "Vekil firma", "attorney_firm_id"),
    ]
    for model, value, label, field in checks:
        if value is not None and db.get(model, value) is None:  # pasif kayıtlar serbest
            raise UnprocessableError(f"{label} bulunamadı ({field}).")


def _check_partners(data: PatentIn) -> None:
    normalized = [normalize_tr(name) for name in data.partners]
    if len(set(normalized)) != len(normalized):
        raise UnprocessableError("Aynı ortak adı birden fazla kez eklenemez.")


def _check_duplicate(db: Session, data: PatentIn, exclude_id: int | None = None) -> None:
    """Aktif patentler arasında normalize başlık + başvuru sahibi + tarih (None == None) eşleşmesi."""
    date_filter = (
        Patent.application_date.is_(None)
        if data.application_date is None
        else Patent.application_date == data.application_date
    )
    candidates = db.execute(
        select(Patent.id, Patent.title).where(
            Patent.deleted_at.is_(None), Patent.applicant_id == data.applicant_id, date_filter
        )
    ).all()
    target = normalize_tr(data.title)
    ids = sorted(pid for pid, title in candidates if pid != exclude_id and normalize_tr(title) == target)
    if ids:
        raise DuplicateWarningError(DUPLICATE_MESSAGE, ids)


def _validate(db: Session, data: PatentIn, confirm_duplicate: bool, exclude_id: int | None = None) -> None:
    _check_references(db, data)
    _check_partners(data)
    if not confirm_duplicate:
        _check_duplicate(db, data, exclude_id)


def create_patent(db: Session, data: PatentIn, confirm_duplicate: bool = False) -> Patent:
    _validate(db, data, confirm_duplicate)
    patent = Patent(
        title=data.title,
        applicant_id=data.applicant_id,
        department_id=data.department_id,
        fsmh_type_id=data.fsmh_type_id,
        attorney_firm_id=data.attorney_firm_id,
        application_date=data.application_date,
        notes=data.notes,
        partners=[PatentPartner(partner_name=name) for name in data.partners],
    )
    db.add(patent)
    commit_or_conflict(db, SAVE_ERROR_MESSAGE)
    db.refresh(patent)
    return patent


def update_patent(db: Session, patent_id: int, data: PatentIn, confirm_duplicate: bool = False) -> Patent:
    patent = get_patent(db, patent_id)
    _validate(db, data, confirm_duplicate, exclude_id=patent_id)
    patent.title = data.title
    patent.applicant_id = data.applicant_id
    patent.department_id = data.department_id
    patent.fsmh_type_id = data.fsmh_type_id
    patent.attorney_firm_id = data.attorney_firm_id
    patent.application_date = data.application_date
    patent.notes = data.notes
    patent.partners = [PatentPartner(partner_name=name) for name in data.partners]  # bütünüyle değişir
    patent.updated_at = utc_now()  # yalnızca ortaklar değişse de ilerlesin
    commit_or_conflict(db, SAVE_ERROR_MESSAGE)
    db.refresh(patent)
    return patent


def delete_patent(db: Session, patent_id: int) -> None:
    """Soft delete: deleted_at doldurulur, satır ve ortaklar veritabanında kalır (Madde 6/1)."""
    patent = get_patent(db, patent_id)
    patent.deleted_at = utc_now()
    commit_or_conflict(db, SAVE_ERROR_MESSAGE)
