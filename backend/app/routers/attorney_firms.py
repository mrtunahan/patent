from fastapi import APIRouter

from app.core.deps import DbSession, ItemId
from app.schemas import LookupSummary, ErrorResponse, AttorneyFirmIn, AttorneyFirmRead
from app.services import attorney_firms as service
from app.services import summaries

router = APIRouter(prefix="/attorney_firms", tags=["attorney_firms"])


@router.get("", response_model=list[AttorneyFirmRead])
def list_attorney_firms(db: DbSession):
    return service.list_attorney_firms(db)


@router.get("/summary", response_model=list[LookupSummary])
def attorney_firms_summary(db: DbSession):
    return summaries.attorney_firms_summary(db)


@router.post("", response_model=AttorneyFirmRead, status_code=201, responses={409: {"model": ErrorResponse}})
def create_attorney_firm(payload: AttorneyFirmIn, db: DbSession):
    return service.create_attorney_firm(db, payload)


@router.get("/{item_id}", response_model=AttorneyFirmRead, responses={404: {"model": ErrorResponse}})
def get_attorney_firm(item_id: ItemId, db: DbSession):
    return service.get_attorney_firm(db, item_id)


@router.put("/{item_id}", response_model=AttorneyFirmRead, responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}})
def update_attorney_firm(item_id: ItemId, payload: AttorneyFirmIn, db: DbSession):
    return service.update_attorney_firm(db, item_id, payload)


@router.delete("/{item_id}", status_code=204, responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}})
def delete_attorney_firm(item_id: ItemId, db: DbSession):
    service.delete_attorney_firm(db, item_id)
