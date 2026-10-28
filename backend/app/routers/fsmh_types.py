from fastapi import APIRouter

from app.core.errors import not_implemented
from app.schemas import FsmhTypeIn, FsmhTypeRead, ErrorResponse

router = APIRouter(prefix="/fsmh_types", tags=["fsmh_types"])


@router.get("", response_model=list[FsmhTypeRead])
def list_fsmh_types():
    not_implemented()


@router.post("", response_model=FsmhTypeRead, status_code=201, responses={409: {"model": ErrorResponse}})
def create_fsmh_type(payload: FsmhTypeIn):
    not_implemented()


@router.get("/{item_id}", response_model=FsmhTypeRead, responses={404: {"model": ErrorResponse}})
def get_fsmh_type(item_id: int):
    not_implemented()


@router.put("/{item_id}", response_model=FsmhTypeRead, responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}})
def update_fsmh_type(item_id: int, payload: FsmhTypeIn):
    not_implemented()


@router.delete("/{item_id}", status_code=204, responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}})
def delete_fsmh_type(item_id: int):
    not_implemented()
