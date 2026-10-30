from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.errors import DuplicateWarningError, NotFoundError, UnprocessableError
from app.core.text import normalize_tr, turkish_sort_key
from app.core.utils import utc_now
from app.models import Applicant, AttorneyFirm, Department, FsmhType, Patent, PatentPartner
from app.schemas import PatentFilterQuery, PatentIn, PatentListQuery, PatentListResponse, PatentRead
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


def _matches_q(patent: Patent, target: str) -> bool:
    """q: başlık, başvuru sahibi adı, ortak adları, notlar içinde normalize alt dize eşleşmesi."""
    fields = [patent.title, patent.applicant.full_name, patent.notes or "", *(p.partner_name for p in patent.partners)]
    return any(target in normalize_tr(field) for field in fields)


def _sort_value(patent: Patent, sort_by: str):
    """Sıralama değeri; None dönerse kayıt (yön ne olursa olsun) sona atılır."""
    match sort_by:
        case "id":
            return patent.id
        case "created_at":
            return patent.created_at
        case "title":
            return turkish_sort_key(patent.title)
        case "applicant":
            return turkish_sort_key(patent.applicant.full_name)
        case "fsmh_type":
            return turkish_sort_key(patent.fsmh_type.name)
        case "department":
            return turkish_sort_key(patent.department.name) if patent.department else None
        case "attorney_firm":
            return turkish_sort_key(patent.attorney_firm.name) if patent.attorney_firm else None
        case "application_date":
            return patent.application_date


def filtered_patents(db: Session, query: PatentFilterQuery) -> list[Patent]:
    """Aktif kayıtlar; filtre ve sıralama uygulanmış, sayfalamasız (liste ve dışa aktarma ortak)."""
    stmt = (
        select(Patent)
        .where(Patent.deleted_at.is_(None))
        .options(
            joinedload(Patent.applicant),
            joinedload(Patent.department),
            joinedload(Patent.fsmh_type),
            joinedload(Patent.attorney_firm),
            selectinload(Patent.partners),  # N+1 yok
        )
        .order_by(Patent.id)
    )
    for column, value in (
        (Patent.applicant_id, query.applicant_id),
        (Patent.department_id, query.department_id),
        (Patent.fsmh_type_id, query.fsmh_type_id),
        (Patent.attorney_firm_id, query.attorney_firm_id),
    ):
        if value is not None:
            stmt = stmt.where(column == value)
    if query.has_attorney is not None:
        stmt = stmt.where(Patent.attorney_firm_id.is_not(None) if query.has_attorney else Patent.attorney_firm_id.is_(None))
    if query.date_from is not None:  # tarihi boş kayıtlar karşılaştırmada elenir
        stmt = stmt.where(Patent.application_date >= query.date_from)
    if query.date_to is not None:
        stmt = stmt.where(Patent.application_date <= query.date_to)

    patents = list(db.scalars(stmt).unique())  # id artan
    if query.q is not None:
        target = normalize_tr(query.q)
        patents = [p for p in patents if _matches_q(p, target)]

    # Eşitlikte id artan: liste id sıralı, Python sort kararlı (reverse=True da eşitlerin sırasını korur).
    keyed = [(p, _sort_value(p, query.sort_by)) for p in patents]
    present = sorted((x for x in keyed if x[1] is not None), key=lambda x: x[1], reverse=query.sort_dir == "desc")
    missing = [x for x in keyed if x[1] is None]  # None her zaman sona (asc ve desc)
    return [p for p, _ in present + missing]


def list_patents(db: Session, query: PatentListQuery) -> PatentListResponse:
    ordered = filtered_patents(db, query)
    start = (query.page - 1) * query.page_size
    page_items = ordered[start : start + query.page_size]
    return PatentListResponse(
        items=[PatentRead.model_validate(p) for p in page_items],
        total=len(ordered),
        page=query.page,
        page_size=query.page_size,
    )
