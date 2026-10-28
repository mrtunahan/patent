from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Setting
from app.services.common import commit_or_conflict


def get_settings(db: Session) -> dict[str, str]:
    return {s.key: s.value for s in db.scalars(select(Setting).order_by(Setting.key))}


def update_settings(db: Session, values: dict[str, str]) -> dict[str, str]:
    """Gönderilen anahtarları ekler/günceller; gönderilmeyenlere dokunmaz."""
    for key, value in values.items():
        setting = db.get(Setting, key)
        if setting is None:
            db.add(Setting(key=key, value=value))
        else:
            setting.value = value
    commit_or_conflict(db, "Ayarlar kaydedilemedi.")
    return get_settings(db)
