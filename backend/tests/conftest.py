from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.config import Settings
from app.database import Base, create_db_engine, get_db
from app.main import create_app
from app.models import Applicant, FsmhType, Patent

ENV_KEYS = ["HOST", "PORT", "CORS_ORIGINS", "FRAME_ANCESTORS", "ROOT_PATH"]


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for key in ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def build_client(engine) -> TestClient:
    """Geçici DB'ye bağlı uygulama (gerçek data/patent.db'ye dokunmaz)."""
    app = create_app(Settings(_env_file=None))

    def override_get_db():
        with Session(engine, expire_on_commit=False) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


@pytest.fixture
def engine(tmp_path):
    eng = create_db_engine(tmp_path / "test.db")
    Base.metadata.create_all(eng)  # yalnızca test; üretimde Alembic
    yield eng
    eng.dispose()


@pytest.fixture
def db(engine):
    with Session(engine, expire_on_commit=False) as session:
        yield session


@pytest.fixture
def client(engine):
    return build_client(engine)


@pytest.fixture
def make_patent(db):
    """Verilen bağlarla bir patent ekler (gerekli başvuru sahibi/tür yoksa oluşturur)."""

    def _make(deleted=False, **links):
        applicant_id = links.pop("applicant_id", None)
        fsmh_type_id = links.pop("fsmh_type_id", None)
        if applicant_id is None:
            applicant = db.query(Applicant).first() or Applicant(full_name="Ali Veli")
            db.add(applicant)
            db.flush()
            applicant_id = applicant.id
        if fsmh_type_id is None:
            fsmh_type = db.query(FsmhType).first() or FsmhType(name="Patent")
            db.add(fsmh_type)
            db.flush()
            fsmh_type_id = fsmh_type.id
        patent = Patent(
            title="T", applicant_id=applicant_id, fsmh_type_id=fsmh_type_id,
            deleted_at=datetime.now(UTC) if deleted else None, **links,
        )
        db.add(patent)
        db.commit()
        return patent

    return _make
