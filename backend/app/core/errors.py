from typing import NoReturn

from fastapi import HTTPException


class NotFoundError(Exception):
    """Kayıt bulunamadı (HTTP bilmez; 404'e main.py'deki handler çevirir)."""


class ConflictError(Exception):
    """İş kuralı çakışması: mükerrer ad, silme engeli vb. (409'a main.py'deki handler çevirir)."""


def not_implemented() -> NoReturn:
    """İskelet endpoint'ler için (gerçek mantık sonraki aşamalarda)."""
    raise HTTPException(status_code=501, detail="Henüz uygulanmadı")
