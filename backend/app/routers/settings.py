from fastapi import APIRouter

from app.core.deps import DbSession
from app.schemas import SettingsMap
from app.services import settings as service

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=dict[str, str])
def get_settings(db: DbSession):
    return service.get_settings(db)


@router.put("", response_model=dict[str, str])
def update_settings(payload: SettingsMap, db: DbSession):
    return service.update_settings(db, payload)
