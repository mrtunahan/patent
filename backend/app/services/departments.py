from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError
from app.core.text import turkish_sort_key
from app.models import Applicant, Department, Patent
from app.schemas import DepartmentIn
from app.services.common import commit_or_conflict, name_taken

DUPLICATE_MESSAGE = "Bu adla bir bölüm zaten var."


def list_departments(db: Session) -> list[Department]:
    departments = db.scalars(select(Department)).all()
    return sorted(departments, key=lambda d: (turkish_sort_key(d.name), d.id))


def get_department(db: Session, department_id: int) -> Department:
    department = db.get(Department, department_id)
    if department is None:
        raise NotFoundError("Bölüm bulunamadı.")
    return department


def create_department(db: Session, data: DepartmentIn) -> Department:
    if name_taken(db, Department, "name", data.name):
        raise ConflictError(DUPLICATE_MESSAGE)
    department = Department(name=data.name)
    db.add(department)
    commit_or_conflict(db, DUPLICATE_MESSAGE)
    db.refresh(department)
    return department


def update_department(db: Session, department_id: int, data: DepartmentIn) -> Department:
    department = get_department(db, department_id)
    if name_taken(db, Department, "name", data.name, exclude_id=department_id):
        raise ConflictError(DUPLICATE_MESSAGE)
    department.name = data.name
    commit_or_conflict(db, DUPLICATE_MESSAGE)
    db.refresh(department)
    return department


def _blocking_reasons(db: Session, department_id: int) -> list[str]:
    reasons = []
    # Silinmiş (deleted_at dolu) patentler dahil: kayıt veritabanında korunduğu için FK bağı sürer.
    if db.scalar(select(func.count()).select_from(Patent).where(Patent.department_id == department_id)):
        reasons.append("bağlı patent kaydı var (silinmiş kayıtlar dahil)")
    if db.scalar(select(func.count()).select_from(Applicant).where(Applicant.department_id == department_id)):
        reasons.append("başvuru sahibi için varsayılan bölüm olarak kullanılıyor")
    return reasons


def delete_department(db: Session, department_id: int) -> None:
    department = get_department(db, department_id)
    reasons = _blocking_reasons(db, department_id)
    if reasons:
        raise ConflictError("Bölüm silinemez: " + ", ".join(reasons) + ".")
    db.delete(department)
    commit_or_conflict(db, "Bölüm başka kayıtlarca kullanıldığı için silinemez.")
