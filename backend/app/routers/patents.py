from typing import Annotated

from fastapi import APIRouter, Query

from app.core.errors import not_implemented
from app.schemas import (
    DuplicateWarning,
    ErrorResponse,
    PatentIn,
    PatentListQuery,
    PatentListResponse,
    PatentRead,
)

router = APIRouter(prefix="/patents", tags=["patents"])

_write_responses = {404: {"model": ErrorResponse}, 409: {"model": DuplicateWarning}}


@router.get("", response_model=PatentListResponse)
def list_patents(query: Annotated[PatentListQuery, Query()]):
    not_implemented()


@router.post("", response_model=PatentRead, status_code=201, responses={409: {"model": DuplicateWarning}})
def create_patent(payload: PatentIn):
    not_implemented()


@router.get("/{patent_id}", response_model=PatentRead, responses={404: {"model": ErrorResponse}})
def get_patent(patent_id: int):
    not_implemented()


@router.put("/{patent_id}", response_model=PatentRead, responses=_write_responses)
def update_patent(patent_id: int, payload: PatentIn):
    not_implemented()


@router.delete("/{patent_id}", status_code=204, responses={404: {"model": ErrorResponse}})
def delete_patent(patent_id: int):
    not_implemented()
