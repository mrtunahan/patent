from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError
from app.core.text import turkish_sort_key
from app.models import Department
from app.schemas import DepartmentIn
from app.services.common import IN_USE_MESSAGE, commit_or_conflict, name_taken

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


def delete_department(db: Session, department_id: int) -> None:
    department = get_department(db, department_id)
    db.delete(department)
    commit_or_conflict(db, IN_USE_MESSAGE)  # bağlı kayıt varsa FK hatası -> 409
