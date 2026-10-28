from datetime import UTC, datetime
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import database
from app.config import Settings
from app.core.errors import ConflictError
from app.database import Base, create_db_engine, get_db
from app.main import create_app
from app.models import Applicant, FsmhType, Patent
from app.schemas import FsmhTypeIn
from app.services import fsmh_types as service

ENV_KEYS = ["HOST", "PORT", "CORS_ORIGINS", "FRAME_ANCESTORS", "ROOT_PATH"]
URL = "/api/fsmh_types"
ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"
SEED = ["Patent", "Faydalı Model", "Tasarım Tescili", "Marka"]


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for key in ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def make_client(engine):
    app = create_app(Settings(_env_file=None))

    def override_get_db():
        with Session(engine, expire_on_commit=False) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


@pytest.fixture
def engine(tmp_path):
    eng = create_db_engine(tmp_path / "fsmh.db")
    Base.metadata.create_all(eng)  # boş tablo; seed yok (yalnızca test)
    yield eng
    eng.dispose()


@pytest.fixture
def migrated_engine(tmp_path):
    """Alembic ile hazırlanmış DB: seed'li 4 tür gelir."""
    eng = create_db_engine(tmp_path / "migrated.db")
    cfg = Config(str(ALEMBIC_INI))
    with eng.begin() as conn:
        cfg.attributes["connection"] = conn
        command.upgrade(cfg, "head")
    yield eng
    eng.dispose()


@pytest.fixture
def db(engine):
    with Session(engine, expire_on_commit=False) as session:
        yield session


@pytest.fixture
def client(engine):
    return make_client(engine)


def post(client, name, sort_order=None):
    body = {"name": name}
    if sort_order is not None:
        body["sort_order"] = sort_order
    return client.post(URL, json=body)


def listing(client):
    return [(t["name"], t["sort_order"]) for t in client.get(URL).json()]


def make_patent(db, fsmh_type_id, deleted=False):
    applicant = db.query(Applicant).first() or Applicant(full_name="Ali Veli")
    db.add(applicant)
    db.flush()
    patent = Patent(
        title="T", applicant_id=applicant.id, fsmh_type_id=fsmh_type_id,
        deleted_at=datetime.now(UTC) if deleted else None,
    )
    db.add(patent)
    db.commit()
    return patent


# --- mutlu yol ---

def test_crud_happy_path(client):
    r = post(client, "Endüstriyel Tasarım", 7)
    assert r.status_code == 201
    body = r.json()
    assert set(body) == {"id", "name", "sort_order", "created_at", "updated_at"}
    assert (body["name"], body["sort_order"]) == ("Endüstriyel Tasarım", 7)
    type_id = body["id"]

    assert client.get(f"{URL}/{type_id}").json()["name"] == "Endüstriyel Tasarım"
    r = client.put(f"{URL}/{type_id}", json={"name": "Coğrafi İşaret", "sort_order": 3})
    assert r.status_code == 200
    assert (r.json()["name"], r.json()["sort_order"], r.json()["id"]) == ("Coğrafi İşaret", 3, type_id)
    assert r.json()["created_at"] == body["created_at"]

    r = client.delete(f"{URL}/{type_id}")
    assert r.status_code == 204 and r.content == b""
    assert client.get(f"{URL}/{type_id}").status_code == 404
    assert client.get(URL).json() == []


def test_sort_order_defaults_to_zero_and_name_trimmed(client):
    r = post(client, "  Faydalı   Model  ")
    assert r.status_code == 201
    assert r.json()["name"] == "Faydalı   Model"  # iç boşluk korunur
    assert r.json()["sort_order"] == 0


def test_put_is_full_replacement_sort_order_resets_to_default(client):
    t = post(client, "Marka", 9).json()
    r = client.put(f"{URL}/{t['id']}", json={"name": "Marka"})  # sort_order verilmedi -> 0
    assert r.status_code == 200 and r.json()["sort_order"] == 0


# --- liste sırası ---

def test_list_order_sort_order_then_turkish_name_then_id(client, db):
    post(client, "Zeta", 1)
    post(client, "Çiçek", 1)
    post(client, "Ankara", 1)
    post(client, "Şu", 0)
    post(client, "Alt", -5)
    post(client, "Işık", 1)
    post(client, "İzmir", 1)
    db.add_all([FsmhType(name="aynı", sort_order=2), FsmhType(name="AYNI", sort_order=2)])  # normalize eşit
    db.commit()
    assert [n for n, _ in listing(client)] == [
        "Alt", "Şu", "Ankara", "Çiçek", "Işık", "İzmir", "Zeta", "aynı", "AYNI",
    ]
    ids = {t["name"]: t["id"] for t in client.get(URL).json()}
    assert ids["aynı"] < ids["AYNI"]


def test_negative_and_update_of_sort_order_changes_position(client):
    a = post(client, "A", 5).json()
    post(client, "B", 1)
    assert [n for n, _ in listing(client)] == ["B", "A"]
    assert client.put(f"{URL}/{a['id']}", json={"name": "A", "sort_order": -3}).json()["sort_order"] == -3
    assert [n for n, _ in listing(client)] == ["A", "B"]


# --- seed (Alembic migration ile) ---

def test_seeded_types_listed_in_order_via_migrated_db(migrated_engine):
    client = make_client(migrated_engine)
    listed = client.get(URL).json()
    assert [(t["name"], t["sort_order"]) for t in listed] == list(zip(SEED, [1, 2, 3, 4]))
    assert all(t["created_at"] and t["updated_at"] for t in listed)


def test_seeded_types_are_not_specially_protected(migrated_engine):
    client = make_client(migrated_engine)
    ids = {t["name"]: t["id"] for t in client.get(URL).json()}
    assert client.delete(f"{URL}/{ids['Marka']}").status_code == 204
    assert client.put(f"{URL}/{ids['Patent']}", json={"name": "Buluş Patenti", "sort_order": 1}).status_code == 200
    assert post(client, "Marka").status_code == 201  # silindikten sonra ad yeniden kullanılabilir


def test_seeded_name_duplicates_are_normalized(migrated_engine):
    client = make_client(migrated_engine)
    for dup in ("FAYDALI  model", "faydalı model", "TASARIM TESCİLİ", "tasarım tescili"):
        assert post(client, dup).status_code == 409, dup


# --- mükerrer ad ---

@pytest.mark.parametrize(
    "first, second",
    [
        ("Faydalı Model", "FAYDALI  model"),
        ("Tasarım Tescili", "TASARIM TESCİLİ"),
        ("Işık", "IŞIK"),
        ("Patent", "patent\t"),
    ],
)
def test_normalized_duplicate_409_post_and_put(client, first, second):
    assert post(client, first).status_code == 201
    r = post(client, second)
    assert r.status_code == 409
    assert r.json() == {"detail": "Bu adla bir FSMH türü zaten var."}
    other = post(client, "Başka Tür").json()
    r = client.put(f"{URL}/{other['id']}", json={"name": second, "sort_order": 4})
    assert r.status_code == 409
    got = client.get(f"{URL}/{other['id']}").json()
    assert (got["name"], got["sort_order"]) == ("Başka Tür", 0)  # rollback: hiçbir şey değişmedi


def test_put_with_own_name_is_ok(client):
    t = post(client, "Faydalı Model", 2).json()
    assert client.put(f"{URL}/{t['id']}", json={"name": "Faydalı Model", "sort_order": 5}).status_code == 200
    r = client.put(f"{URL}/{t['id']}", json={"name": "FAYDALI MODEL", "sort_order": 5})
    assert r.status_code == 200 and r.json()["name"] == "FAYDALI MODEL"
    assert len(client.get(URL).json()) == 1


def test_turkish_i_rule_and_no_accent_folding_not_duplicates(client):
    assert post(client, "Isparta").status_code == 201
    assert post(client, "isparta").status_code == 201
    assert post(client, "Şu").status_code == 201
    assert post(client, "Su").status_code == 201


# --- 404 ---

def test_not_found(client):
    for r in (client.get(f"{URL}/999"), client.put(f"{URL}/999", json={"name": "X"}), client.delete(f"{URL}/999")):
        assert r.status_code == 404
        assert r.json() == {"detail": "Tür bulunamadı."}


# --- silme engeli ---

def test_delete_blocked_by_active_patent(client, db):
    t = post(client, "Özel").json()
    make_patent(db, t["id"])
    r = client.delete(f"{URL}/{t['id']}")
    assert r.status_code == 409
    assert r.json() == {"detail": "FSMH türü silinemez: bağlı patent kaydı var (silinmiş kayıtlar dahil)."}
    assert client.get(f"{URL}/{t['id']}").status_code == 200


def test_delete_blocked_by_soft_deleted_patent(client, db):
    t = post(client, "Özel").json()
    make_patent(db, t["id"], deleted=True)
    r = client.delete(f"{URL}/{t['id']}")
    assert r.status_code == 409
    # ön kontrol mesajı (FK yarış mesajı değil): silinmiş patentler de sayılıyor
    assert r.json() == {"detail": "FSMH türü silinemez: bağlı patent kaydı var (silinmiş kayıtlar dahil)."}
    assert client.get(f"{URL}/{t['id']}").status_code == 200


def test_delete_ok_without_links_and_other_types_links_do_not_block(client, db):
    linked = post(client, "Bağlı").json()
    free = post(client, "Serbest").json()
    make_patent(db, linked["id"])
    assert client.delete(f"{URL}/{free['id']}").status_code == 204
    assert [n for n, _ in listing(client)] == ["Bağlı"]
    assert db.query(FsmhType).filter_by(name="Serbest").count() == 0


# --- 422 ---

@pytest.mark.parametrize(
    "body",
    [
        {"name": ""}, {"name": "   "}, {}, {"name": 5},
        {"name": "A", "id": 3}, {"name": "A", "created_at": "x"},
        {"name": "A", "sort_order": "abc"}, {"name": "A", "sort_order": 1.5}, {"name": "A", "sort_order": None},
    ],
)
def test_invalid_body_422(client, body):
    assert client.post(URL, json=body).status_code == 422
    assert client.put(f"{URL}/1", json=body).status_code == 422


def test_name_length_boundary_100(client):
    assert post(client, "a" * 100).status_code == 201
    assert post(client, "b" * 101).status_code == 422
    assert client.get(f"{URL}/abc").status_code == 422


def test_sort_order_beyond_sqlite_integer_is_422_not_500(client):
    assert post(client, "Büyük", 2**31 - 1).status_code == 201
    assert post(client, "Küçük", -(2**31)).status_code == 201
    assert post(client, "Taşan", 2**31).status_code == 422
    assert post(client, "Taşan", -(2**31) - 1).status_code == 422
    assert post(client, "Taşan", 10**30).status_code == 422


# --- yarış emniyeti ---

def test_service_unique_race_becomes_conflict_and_session_stays_usable(db, monkeypatch):
    monkeypatch.setattr(service, "name_taken", lambda *a, **k: False)
    service.create_fsmh_type(db, FsmhTypeIn(name="Marka"))
    with pytest.raises(ConflictError, match="zaten var"):
        service.create_fsmh_type(db, FsmhTypeIn(name="Marka"))
    assert [t.name for t in service.list_fsmh_types(db)] == ["Marka"]
    other = service.create_fsmh_type(db, FsmhTypeIn(name="Patent"))
    with pytest.raises(ConflictError):
        service.update_fsmh_type(db, other.id, FsmhTypeIn(name="Marka"))
    assert service.get_fsmh_type(db, other.id).name == "Patent"


def test_service_delete_fk_race_becomes_conflict(db, monkeypatch):
    t = service.create_fsmh_type(db, FsmhTypeIn(name="Marka"))
    make_patent(db, t.id)
    monkeypatch.setattr(service, "_has_patents", lambda *a, **k: False)
    with pytest.raises(ConflictError, match="başka kayıtlarca"):
        service.delete_fsmh_type(db, t.id)
    assert service.get_fsmh_type(db, t.id).name == "Marka"


# --- başlıklar ---

def test_frame_ancestors_on_all_fsmh_type_responses(client, db):
    t = post(client, "Bağlı").json()
    make_patent(db, t["id"])
    responses = [
        post(client, "Yeni"),                     # 201
        post(client, "yeni"),                     # 409 mükerrer
        client.delete(f"{URL}/{t['id']}"),        # 409 silme engeli
        client.get(f"{URL}/999"),                 # 404
        client.post(URL, json={"name": ""}),      # 422
        client.get(URL),                          # 200
        client.delete(f"{URL}/{post(client, 'Silinecek').json()['id']}"),  # 204
    ]
    assert [r.status_code for r in responses] == [201, 409, 409, 404, 422, 200, 204]
    for r in responses:
        assert r.headers["content-security-policy"] == "frame-ancestors 'self'"
        assert "x-frame-options" not in r.headers


def test_openapi_documents_fsmh_type_routes(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert {"get", "post"} <= set(paths["/api/fsmh_types"])
    assert {"get", "put", "delete"} <= set(paths["/api/fsmh_types/{item_id}"])
    assert "409" in paths["/api/fsmh_types"]["post"]["responses"]
    assert {"404", "409"} <= set(paths["/api/fsmh_types/{item_id}"]["delete"]["responses"])


def test_tests_never_touch_real_database_file(client):
    existed = database.DB_PATH.exists()
    post(client, "X")
    assert database.DB_PATH.exists() == existed
