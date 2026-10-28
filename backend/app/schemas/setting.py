from typing import Annotated

from pydantic import BeforeValidator, StringConstraints

SettingKey = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
SettingValue = Annotated[str, StringConstraints(strip_whitespace=True)]  # boş string geçerli


def _reject_colliding_keys(value):
    """Kırpma sonrası aynı olan anahtarlar sessizce birbirini ezmesin."""
    if isinstance(value, dict):
        stripped = [k.strip() if isinstance(k, str) else k for k in value]
        if len(set(stripped)) != len(stripped):
            raise ValueError("Kırpma sonrası tekrar eden ayar anahtarı var")
    return value


# GET yanıtı ve PUT gövdesi: {anahtar: değer}
SettingsMap = Annotated[dict[SettingKey, SettingValue], BeforeValidator(_reject_colliding_keys)]
