from typing import NoReturn

from fastapi import HTTPException


class NotFoundError(Exception):
    """Kayıt bulunamadı (HTTP bilmez; 404'e main.py'deki handler çevirir)."""


class ConflictError(Exception):
    """İş kuralı çakışması: mükerrer ad, silme engeli vb. (409'a main.py'deki handler çevirir)."""


class UnprocessableError(Exception):
    """İstek geçerli biçimde ama içeriği kabul edilemez, örn. var olmayan ilişkili kayıt (422)."""


class DuplicateWarningError(Exception):
    """Mükerrer patent uyarısı (Madde 6/4): engellemez, onayla kaydedilir. 409 + DuplicateWarning gövdesi."""

    def __init__(self, message: str, existing_ids: list[int]) -> None:
        super().__init__(message)
        self.existing_ids = existing_ids


def not_implemented() -> NoReturn:
    """İskelet endpoint'ler için (gerçek mantık sonraki aşamalarda)."""
    raise HTTPException(status_code=501, detail="Henüz uygulanmadı")
