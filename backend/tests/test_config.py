from pathlib import Path

import pytest
from pydantic import ValidationError

from app.config import Settings

ENV_EXAMPLE = Path(__file__).resolve().parents[2] / ".env.example"
ENV_KEYS = ["HOST", "PORT", "CORS_ORIGINS", "FRAME_ANCESTORS", "ROOT_PATH"]


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for key in ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def test_defaults():
    s = Settings(_env_file=None)
    assert s.HOST == "127.0.0.1"
    assert s.PORT == 8001
    assert s.CORS_ORIGINS == []
    assert s.FRAME_ANCESTORS == "'self'"
    assert s.ROOT_PATH == ""


def test_env_example_loads_quoted_self():
    s = Settings(_env_file=ENV_EXAMPLE)
    assert s.FRAME_ANCESTORS == "'self'"
    assert s.CORS_ORIGINS == ["http://localhost:5173", "http://127.0.0.1:5173"]
    assert s.PORT == 8001
    assert s.ROOT_PATH == ""


def test_frame_ancestors_multiple_sources_allowed():
    s = Settings(_env_file=None, FRAME_ANCESTORS="'self' https://ana.example.edu.tr")
    assert s.FRAME_ANCESTORS == "'self' https://ana.example.edu.tr"


@pytest.mark.parametrize(
    "bad", ["'self'; script-src *", "'self'\nX-Evil: 1", "'self'\r\nX-Evil: 1", "a\rb"]
)
def test_frame_ancestors_rejects_injection(bad):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, FRAME_ANCESTORS=bad)


def test_frame_ancestors_rejected_from_environment(monkeypatch):
    monkeypatch.setenv("FRAME_ANCESTORS", "'self'; default-src *")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)
