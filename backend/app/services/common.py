from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import ConflictError
from app.core.text import normalize_tr
from app.models import Applicant, Patent


def name_taken(db: Session, model, column: str, value: str, exclude_id: int | None = None) -> bool:
    """`column` değeri normalize_tr ile başka bir kayıtla eşleşiyor mu (mükerrer kontrolü).

    Lookup tabloları küçük olduğu için adlar Python tarafında karşılaştırılır
    (SQLite lower() Türkçe harfleri doğru işlemez).
    """
    target = normalize_tr(value)
    rows = db.execute(select(model.id, getattr(model, column))).all()
    return any(row_id != exclude_id and normalize_tr(name) == target for row_id, name in rows)


IN_USE_MESSAGE = "Bu kayıt başka kayıtlarca kullanıldığı için silinemez."


def commit_or_conflict(db: Session, message: str) -> None:
    """Commit eder; IntegrityError'da (UNIQUE/FK) rollback yapıp 500 yerine ConflictError üretir.

    Silmede IN_USE_MESSAGE verilir (FK: foreign_keys=ON ile bağlı kayıt), ekleme/güncellemede
    ilgili "Bu adla ... zaten var." mesajı.
    """
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(message) from exc


def delete_lookup(db: Session, record, patent_column, department: bool = False) -> None:
    """Lookup kaydını siler (Madde 6/2 kısmi): aktif patent bağlıysa 409; yalnızca SİLİNMİŞ patentler bağlıysa
    onlar (ortaklarıyla, CASCADE) fiziksel silinip kayıt silinir. Tek transaction; hata olursa geri alınır.
    `department=True`: bölümü varsayılan bölüm olarak kullanan başvuru sahipleri de engel sayılır.
    """
    messages = []
    active = db.scalar(select(func.count()).select_from(Patent).where(patent_column == record.id, Patent.deleted_at.is_(None)))
    if active:
        messages.append(f"Bu kayıt {active} aktif patentte kullanılıyor, silinemez.")
    if department:
        users = db.scalar(select(func.count()).select_from(Applicant).where(Applicant.department_id == record.id))
        if users:
            messages.append(f"Bu bölüm {users} başvuru sahibinin varsayılan bölümü olarak kullanılıyor, silinemez.")
    if messages:
        raise ConflictError(" ".join(messages))
    db.execute(delete(Patent).where(patent_column == record.id, Patent.deleted_at.is_not(None)))
    db.delete(record)
    commit_or_conflict(db, IN_USE_MESSAGE)  # beklenmeyen FK hatası için yedek mesaj
