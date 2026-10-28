from fastapi import APIRouter

from app.core.deps import DbSession, ItemId
from app.schemas import DepartmentIn, DepartmentRead, ErrorResponse
from app.services import departments as service

router = APIRouter(prefix="/departments", tags=["departments"])


@router.get("", response_model=list[DepartmentRead])
def list_departments(db: DbSession):
    return service.list_departments(db)


@router.post("", response_model=DepartmentRead, status_code=201, responses={409: {"model": ErrorResponse}})
def create_department(payload: DepartmentIn, db: DbSession):
    return service.create_department(db, payload)


@router.get("/{item_id}", response_model=DepartmentRead, responses={404: {"model": ErrorResponse}})
def get_department(item_id: ItemId, db: DbSession):
    return service.get_department(db, item_id)


@router.put("/{item_id}", response_model=DepartmentRead, responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}})
def update_department(item_id: ItemId, payload: DepartmentIn, db: DbSession):
    return service.update_department(db, item_id, payload)


@router.delete("/{item_id}", status_code=204, responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}})
def delete_department(item_id: ItemId, db: DbSession):
    service.delete_department(db, item_id)
