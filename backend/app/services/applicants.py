from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError, UnprocessableError
from app.core.text import turkish_sort_key
from app.models import Applicant, Department, Patent
from app.schemas import ApplicantIn
from app.services.common import commit_or_conflict, delete_lookup, name_taken

DUPLICATE_MESSAGE = "Bu adla bir başvuru sahibi zaten var."


def list_applicants(db: Session) -> list[Applicant]:
    applicants = db.scalars(select(Applicant)).all()
    return sorted(applicants, key=lambda a: (turkish_sort_key(a.full_name), a.id))


def get_applicant(db: Session, applicant_id: int) -> Applicant:
    applicant = db.get(Applicant, applicant_id)
    if applicant is None:
        raise NotFoundError("Başvuru sahibi bulunamadı.")
    return applicant


def _check_department(db: Session, department_id: int | None) -> None:
    if department_id is not None and db.get(Department, department_id) is None:
        raise UnprocessableError("Bölüm bulunamadı (department_id).")


def create_applicant(db: Session, data: ApplicantIn) -> Applicant:
    _check_department(db, data.department_id)
    if name_taken(db, Applicant, "full_name", data.full_name):
        raise ConflictError(DUPLICATE_MESSAGE)
    applicant = Applicant(
        full_name=data.full_name, department_id=data.department_id, email=data.email, is_active=data.is_active
    )
    db.add(applicant)
    commit_or_conflict(db, DUPLICATE_MESSAGE)
    db.refresh(applicant)
    return applicant


def update_applicant(db: Session, applicant_id: int, data: ApplicantIn) -> Applicant:
    applicant = get_applicant(db, applicant_id)
    _check_department(db, data.department_id)
    if name_taken(db, Applicant, "full_name", data.full_name, exclude_id=applicant_id):
        raise ConflictError(DUPLICATE_MESSAGE)
    applicant.full_name = data.full_name
    applicant.department_id = data.department_id
    applicant.email = data.email
    applicant.is_active = data.is_active
    commit_or_conflict(db, DUPLICATE_MESSAGE)
    db.refresh(applicant)
    return applicant


def delete_applicant(db: Session, applicant_id: int) -> None:
    applicant = get_applicant(db, applicant_id)
    delete_lookup(db, applicant, Patent.applicant_id)
