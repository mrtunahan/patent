from fastapi import APIRouter

from app.core.deps import DbSession
from app.schemas import ErrorResponse, FsmhTypeIn, FsmhTypeRead
from app.services import fsmh_types as service

router = APIRouter(prefix="/fsmh_types", tags=["fsmh_types"])


@router.get("", response_model=list[FsmhTypeRead])
def list_fsmh_types(db: DbSession):
    return service.list_fsmh_types(db)


@router.post("", response_model=FsmhTypeRead, status_code=201, responses={409: {"model": ErrorResponse}})
def create_fsmh_type(payload: FsmhTypeIn, db: DbSession):
    return service.create_fsmh_type(db, payload)


@router.get("/{item_id}", response_model=FsmhTypeRead, responses={404: {"model": ErrorResponse}})
def get_fsmh_type(item_id: int, db: DbSession):
    return service.get_fsmh_type(db, item_id)


@router.put("/{item_id}", response_model=FsmhTypeRead, responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}})
def update_fsmh_type(item_id: int, payload: FsmhTypeIn, db: DbSession):
    return service.update_fsmh_type(db, item_id, payload)


@router.delete("/{item_id}", status_code=204, responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}})
def delete_fsmh_type(item_id: int, db: DbSession):
    service.delete_fsmh_type(db, item_id)
