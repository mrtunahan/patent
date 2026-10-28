from fastapi import APIRouter

from app.core.errors import not_implemented
from app.schemas import SettingsMap

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SettingsMap)
def get_settings():
    not_implemented()


@router.put("", response_model=SettingsMap)
def update_settings(payload: SettingsMap):
    not_implemented()
