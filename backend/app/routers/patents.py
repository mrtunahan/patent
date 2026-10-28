from typing import Annotated

from fastapi import APIRouter, Query

from app.core.deps import DbSession, ItemId
from app.schemas import (
    DuplicateWarning,
    ErrorResponse,
    PatentIn,
    PatentListQuery,
    PatentListResponse,
    PatentRead,
)
from app.services import patents as service

router = APIRouter(prefix="/patents", tags=["patents"])

_duplicate = {409: {"model": DuplicateWarning}}


@router.get("", response_model=PatentListResponse)
def list_patents(query: Annotated[PatentListQuery, Query()], db: DbSession):
    return service.list_patents(db, query)


@router.post("", response_model=PatentRead, status_code=201, responses=_duplicate)
def create_patent(payload: PatentIn, db: DbSession, confirm_duplicate: bool = False):
    return service.create_patent(db, payload, confirm_duplicate)


@router.get("/{patent_id}", response_model=PatentRead, responses={404: {"model": ErrorResponse}})
def get_patent(patent_id: ItemId, db: DbSession):
    return service.get_patent(db, patent_id)


@router.put("/{patent_id}", response_model=PatentRead, responses={404: {"model": ErrorResponse}, **_duplicate})
def update_patent(patent_id: ItemId, payload: PatentIn, db: DbSession, confirm_duplicate: bool = False):
    return service.update_patent(db, patent_id, payload, confirm_duplicate)


@router.delete("/{patent_id}", status_code=204, responses={404: {"model": ErrorResponse}})
def delete_patent(patent_id: ItemId, db: DbSession):
    service.delete_patent(db, patent_id)
