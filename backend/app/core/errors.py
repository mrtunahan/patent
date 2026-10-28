from typing import NoReturn

from fastapi import HTTPException


def not_implemented() -> NoReturn:
    """İskelet endpoint'ler için (gerçek mantık sonraki aşamalarda)."""
    raise HTTPException(status_code=501, detail="Henüz uygulanmadı")
