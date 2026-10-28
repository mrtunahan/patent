from fastapi import APIRouter

from app.core.errors import not_implemented
from app.schemas import ApplicantIn, ApplicantRead, ErrorResponse

router = APIRouter(prefix="/applicants", tags=["applicants"])


@router.get("", response_model=list[ApplicantRead])
def list_applicants():
    not_implemented()


@router.post("", response_model=ApplicantRead, status_code=201, responses={409: {"model": ErrorResponse}})
def create_applicant(payload: ApplicantIn):
    not_implemented()


@router.get("/{item_id}", response_model=ApplicantRead, responses={404: {"model": ErrorResponse}})
def get_applicant(item_id: int):
    not_implemented()


@router.put("/{item_id}", response_model=ApplicantRead, responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}})
def update_applicant(item_id: int, payload: ApplicantIn):
    not_implemented()


@router.delete("/{item_id}", status_code=204, responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}})
def delete_applicant(item_id: int):
    not_implemented()
