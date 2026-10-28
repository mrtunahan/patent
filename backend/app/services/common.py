from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import ConflictError
from app.core.text import normalize_tr


def name_taken(db: Session, model, column: str, value: str, exclude_id: int | None = None) -> bool:
    """`column` değeri normalize_tr ile başka bir kayıtla eşleşiyor mu (mükerrer kontrolü).

    Lookup tabloları küçük olduğu için adlar Python tarafında karşılaştırılır
    (SQLite lower() Türkçe harfleri doğru işlemez).
    """
    target = normalize_tr(value)
    rows = db.execute(select(model.id, getattr(model, column))).all()
    return any(row_id != exclude_id and normalize_tr(name) == target for row_id, name in rows)


def commit_or_conflict(db: Session, message: str) -> None:
    """Commit eder; UNIQUE/FK ihlalinde (örn. yarış durumu) rollback yapıp ConflictError üretir."""
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(message) from exc
