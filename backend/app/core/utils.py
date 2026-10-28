from datetime import UTC, datetime


def utc_now() -> datetime:
    """Zaman damgaları için tek UTC kaynağı (SQLite'a UTC duvar saati olarak yazılır)."""
    return datetime.now(UTC)
