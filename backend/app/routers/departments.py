from fastapi import APIRouter

from app.core.errors import not_implemented
from app.schemas import DepartmentIn, DepartmentRead, ErrorResponse

router = APIRouter(prefix="/departments", tags=["departments"])


@router.get("", response_model=list[DepartmentRead])
def list_departments():
    not_implemented()


@router.post("", response_model=DepartmentRead, status_code=201, responses={409: {"model": ErrorResponse}})
def create_department(payload: DepartmentIn):
    not_implemented()


@router.get("/{item_id}", response_model=DepartmentRead, responses={404: {"model": ErrorResponse}})
def get_department(item_id: int):
    not_implemented()


@router.put("/{item_id}", response_model=DepartmentRead, responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}})
def update_department(item_id: int, payload: DepartmentIn):
    not_implemented()


@router.delete("/{item_id}", status_code=204, responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}})
def delete_department(item_id: int):
    not_implemented()
