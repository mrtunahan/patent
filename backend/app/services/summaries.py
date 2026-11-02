from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.text import normalize_tr, turkish_sort_key
from app.models import Applicant, AttorneyFirm, Department, Patent, PatentPartner
from app.schemas import ApplicantSummary, LookupSummary, PartnerSummary, PatentRef


def _refs(patents: list[tuple[int, str]]) -> list[PatentRef]:
    return [PatentRef(id=pid, title=title) for pid, title in sorted(patents)]


def partners_summary(db: Session) -> list[PartnerSummary]:
    """Ortaklar ayrı tablo değildir: aktif patentlerin ortak adları normalize_tr ile gruplanır.

    Görünen ad, grubun en küçük id'li kaydındaki yazımdır.
    """
    rows = db.execute(
        select(PatentPartner.partner_name, Patent.id, Patent.title)
        .join(Patent, Patent.id == PatentPartner.patent_id)
        .where(Patent.deleted_at.is_(None))
        .order_by(PatentPartner.id)
    ).all()
    display: dict[str, str] = {}
    patents: dict[str, dict[int, str]] = defaultdict(dict)
    for name, patent_id, title in rows:
        key = normalize_tr(name)
        display.setdefault(key, name)
        patents[key][patent_id] = title
    result = [
        PartnerSummary(name=display[key], patent_count=len(items), patents=_refs(list(items.items())))
        for key, items in patents.items()
    ]
    return sorted(result, key=lambda p: turkish_sort_key(p.name))


def _lookup_summary(db: Session, model, column, name_attr: str = "name") -> list[LookupSummary]:
    """Tüm kayıtlar (0 patentli dahil); sayım yalnızca aktif patentler üzerinden."""
    linked: dict[int, list[tuple[int, str]]] = defaultdict(list)
    for owner_id, patent_id, title in db.execute(
        select(column, Patent.id, Patent.title).where(Patent.deleted_at.is_(None), column.is_not(None))
    ):
        linked[owner_id].append((patent_id, title))
    result = [
        LookupSummary(id=r.id, name=getattr(r, name_attr), patent_count=len(linked[r.id]), patents=_refs(linked[r.id]))
        for r in db.scalars(select(model))
    ]
    return sorted(result, key=lambda s: (turkish_sort_key(s.name), s.id))


def departments_summary(db: Session) -> list[LookupSummary]:
    return _lookup_summary(db, Department, Patent.department_id)


def attorney_firms_summary(db: Session) -> list[LookupSummary]:
    return _lookup_summary(db, AttorneyFirm, Patent.attorney_firm_id)


def applicants_summary(db: Session) -> list[ApplicantSummary]:
    return [
        ApplicantSummary(id=x.id, full_name=x.name, patent_count=x.patent_count, patents=x.patents)
        for x in _lookup_summary(db, Applicant, Patent.applicant_id, "full_name")  # sıralama full_name'e göre
    ]
