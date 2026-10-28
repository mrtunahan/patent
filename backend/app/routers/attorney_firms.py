from fastapi import APIRouter

from app.core.errors import not_implemented
from app.schemas import AttorneyFirmIn, AttorneyFirmRead, ErrorResponse

router = APIRouter(prefix="/attorney_firms", tags=["attorney_firms"])


@router.get("", response_model=list[AttorneyFirmRead])
def list_attorney_firms():
    not_implemented()


@router.post("", response_model=AttorneyFirmRead, status_code=201, responses={409: {"model": ErrorResponse}})
def create_attorney_firm(payload: AttorneyFirmIn):
    not_implemented()


@router.get("/{item_id}", response_model=AttorneyFirmRead, responses={404: {"model": ErrorResponse}})
def get_attorney_firm(item_id: int):
    not_implemented()


@router.put("/{item_id}", response_model=AttorneyFirmRead, responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}})
def update_attorney_firm(item_id: int, payload: AttorneyFirmIn):
    not_implemented()


@router.delete("/{item_id}", status_code=204, responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}})
def delete_attorney_firm(item_id: int):
    not_implemented()
