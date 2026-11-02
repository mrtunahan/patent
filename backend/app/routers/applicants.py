from fastapi import APIRouter

from app.core.deps import DbSession, ItemId
from app.schemas import ApplicantSummary, ErrorResponse, ApplicantIn, ApplicantRead
from app.services import applicants as service
from app.services import summaries

router = APIRouter(prefix="/applicants", tags=["applicants"])


@router.get("", response_model=list[ApplicantRead])
def list_applicants(db: DbSession):
    return service.list_applicants(db)


@router.get("/summary", response_model=list[ApplicantSummary])
def applicants_summary(db: DbSession):
    return summaries.applicants_summary(db)


@router.post("", response_model=ApplicantRead, status_code=201, responses={409: {"model": ErrorResponse}})
def create_applicant(payload: ApplicantIn, db: DbSession):
    return service.create_applicant(db, payload)


@router.get("/{item_id}", response_model=ApplicantRead, responses={404: {"model": ErrorResponse}})
def get_applicant(item_id: ItemId, db: DbSession):
    return service.get_applicant(db, item_id)


@router.put("/{item_id}", response_model=ApplicantRead, responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}})
def update_applicant(item_id: ItemId, payload: ApplicantIn, db: DbSession):
    return service.update_applicant(db, item_id, payload)


@router.delete("/{item_id}", status_code=204, responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}})
def delete_applicant(item_id: ItemId, db: DbSession):
    service.delete_applicant(db, item_id)
