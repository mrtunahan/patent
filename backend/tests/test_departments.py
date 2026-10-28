from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import database
from app.config import Settings
from app.core.errors import ConflictError, NotFoundError
from app.database import Base, create_db_engine, get_db
from app.main import create_app
from app.models import Applicant, Department, FsmhType, Patent
from app.schemas import DepartmentIn
from app.services import departments as service

ENV_KEYS = ["HOST", "PORT", "CORS_ORIGINS", "FRAME_ANCESTORS", "ROOT_PATH"]
URL = "/api/departments"


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for key in ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


@pytest.fixture
def engine(tmp_path):
    eng = create_db_engine(tmp_path / "departments.db")
    Base.metadata.create_all(eng)  # yalnızca test; üretimde Alembic
    yield eng
    eng.dispose()


@pytest.fixture
def db(engine):
    with Session(engine, expire_on_commit=False) as session:
        yield session


@pytest.fixture
def client(engine):
    app = create_app(Settings(_env_file=None))

    def override_get_db():
        with Session(engine, expire_on_commit=False) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def post(client, name):
    return client.post(URL, json={"name": name})


def names(client):
    return [d["name"] for d in client.get(URL).json()]


def make_patent(db, department_id, deleted=False):
    applicant = db.query(Applicant).first() or Applicant(full_name="Ali Veli")
    ftype = db.query(FsmhType).first() or FsmhType(name="Patent")
    db.add_all([applicant, ftype])
    db.flush()
    patent = Patent(
        title="T", applicant_id=applicant.id, fsmh_type_id=ftype.id, department_id=department_id,
        deleted_at=datetime.now(UTC) if deleted else None,
    )
    db.add(patent)
    db.commit()
    return patent


# --- mutlu yol ---

def test_crud_happy_path(client):
    r = post(client, "Peyzaj Mimarlığı")
    assert r.status_code == 201
    body = r.json()
    assert set(body) == {"id", "name", "created_at", "updated_at"}
    assert body["name"] == "Peyzaj Mimarlığı"
    assert body["created_at"].endswith(("Z", "+00:00"))
    dept_id = body["id"]

    assert client.get(f"{URL}/{dept_id}").json()["name"] == "Peyzaj Mimarlığı"
    assert [d["id"] for d in client.get(URL).json()] == [dept_id]

    r = client.put(f"{URL}/{dept_id}", json={"name": "Peyzaj Mimarlığı Bölümü"})
    assert r.status_code == 200
    assert r.json()["name"] == "Peyzaj Mimarlığı Bölümü"
    assert r.json()["id"] == dept_id
    assert client.get(f"{URL}/{dept_id}").json()["name"] == "Peyzaj Mimarlığı Bölümü"

    r = client.delete(f"{URL}/{dept_id}")
    assert r.status_code == 204 and r.content == b""
    assert client.get(f"{URL}/{dept_id}").status_code == 404
    assert client.get(URL).json() == []


def test_update_changes_updated_at_not_created_at(client):
    created = post(client, "A").json()
    updated = client.put(f"{URL}/{created['id']}", json={"name": "B"}).json()
    assert updated["created_at"] == created["created_at"]
    assert updated["updated_at"] >= created["updated_at"]


def test_name_is_trimmed_inner_spaces_and_spelling_preserved(client):
    r = post(client, "  Peyzaj   Mimarlığı  ")
    assert r.status_code == 201
    assert r.json()["name"] == "Peyzaj   Mimarlığı"  # iç boşluk ve yazım aynen
    r = post(client, "ŞABANÖZÜ MYO")
    assert r.json()["name"] == "ŞABANÖZÜ MYO"  # büyük harf aynen saklanır


# --- liste: Türkçe duyarlı sıralama ---

def test_list_is_sorted_by_turkish_alphabet(client):
    for name in ["Zonguldak MYO", "Çankırı Mühendislik", "Ankara", "Şabanözü MYO", "Sivas", "Ödemiş",
                 "Işık Meslek", "İzmir", "Ulus", "Üsküdar", "Gazi"]:
        assert post(client, name).status_code == 201
    assert names(client) == [
        "Ankara", "Çankırı Mühendislik", "Gazi", "Işık Meslek", "İzmir", "Ödemiş",
        "Sivas", "Şabanözü MYO", "Ulus", "Üsküdar", "Zonguldak MYO",
    ]


def test_list_sort_is_case_insensitive_and_ties_broken_by_id(db, client):
    # ham UNIQUE farklı ama normalize edilmiş eşit iki ad (servis kontrolünü atlayarak eklenir)
    first = Department(name="aynı")
    second = Department(name="AYNI")
    db.add_all([first, second])
    db.commit()
    post(client, "Başka")
    listed = client.get(URL).json()
    assert [d["name"] for d in listed] == ["aynı", "AYNI", "Başka"]
    assert listed[0]["id"] < listed[1]["id"]


# --- mükerrer ad (normalize edilmiş) ---

@pytest.mark.parametrize(
    "first, second",
    [
        ("Peyzaj Mimarlığı", "peyzaj  mimarlığı"),
        ("Peyzaj Mimarlığı", "PEYZAJ MİMARLIĞI"),
        ("IŞIK", "ışık"),
        ("ışık", "IŞIK"),
        ("İstanbul", "istanbul"),
        ("Çankırı", "ÇANKIRI"),
        ("Şabanözü MYO", "şabanözü\tmyo"),
        ("Tasarım Tescili", "tasarım tescili"),
    ],
)
def test_normalized_duplicate_is_409_on_post(client, first, second):
    assert post(client, first).status_code == 201
    r = post(client, second)
    assert r.status_code == 409
    assert r.json() == {"detail": "Bu adla bir bölüm zaten var."}
    assert len(client.get(URL).json()) == 1


def test_turkish_case_rules_and_no_accent_folding_are_not_duplicates(client):
    assert post(client, "Isparta").status_code == 201
    assert post(client, "isparta").status_code == 201  # I -> ı, i -> i: farklı
    assert post(client, "Şaban").status_code == 201
    assert post(client, "Saban").status_code == 201  # aksan katlanmaz
    assert len(client.get(URL).json()) == 4


def test_normalized_duplicate_is_409_on_put(client):
    a = post(client, "Peyzaj Mimarlığı").json()
    b = post(client, "Bilgisayar").json()
    r = client.put(f"{URL}/{b['id']}", json={"name": "peyzaj   MİMARLIĞI"})
    assert r.status_code == 409
    assert r.json() == {"detail": "Bu adla bir bölüm zaten var."}
    assert client.get(f"{URL}/{b['id']}").json()["name"] == "Bilgisayar"  # değişmedi
    assert client.get(f"{URL}/{a['id']}").json()["name"] == "Peyzaj Mimarlığı"


def test_put_with_own_name_is_ok_even_if_only_case_changes(client):
    a = post(client, "Peyzaj Mimarlığı").json()
    assert client.put(f"{URL}/{a['id']}", json={"name": "Peyzaj Mimarlığı"}).status_code == 200
    r = client.put(f"{URL}/{a['id']}", json={"name": "PEYZAJ MİMARLIĞI"})
    assert r.status_code == 200
    assert r.json()["name"] == "PEYZAJ MİMARLIĞI"  # yazım kullanıcının girdiği gibi
    assert len(client.get(URL).json()) == 1


# --- 404 ---

def test_not_found(client):
    for r in (client.get(f"{URL}/999"), client.put(f"{URL}/999", json={"name": "X"}), client.delete(f"{URL}/999")):
        assert r.status_code == 404
        assert r.json() == {"detail": "Bölüm bulunamadı."}


# --- silme engeli ---

def test_delete_blocked_by_active_patent(client, db):
    dept = post(client, "Peyzaj").json()
    make_patent(db, dept["id"])
    r = client.delete(f"{URL}/{dept['id']}")
    assert r.status_code == 409
    assert "patent" in r.json()["detail"]
    assert client.get(f"{URL}/{dept['id']}").status_code == 200


def test_delete_blocked_by_soft_deleted_patent(client, db):
    dept = post(client, "Peyzaj").json()
    make_patent(db, dept["id"], deleted=True)
    r = client.delete(f"{URL}/{dept['id']}")
    assert r.status_code == 409
    assert "silinmiş kayıtlar dahil" in r.json()["detail"]
    assert client.get(f"{URL}/{dept['id']}").status_code == 200


def test_delete_blocked_by_applicant_default_department(client, db):
    dept = post(client, "Peyzaj").json()
    db.add(Applicant(full_name="Ayşe", department_id=dept["id"]))
    db.commit()
    r = client.delete(f"{URL}/{dept['id']}")
    assert r.status_code == 409
    assert "başvuru sahibi" in r.json()["detail"]
    assert client.get(f"{URL}/{dept['id']}").status_code == 200


def test_delete_blocked_message_names_every_blocker(client, db):
    dept = post(client, "Peyzaj").json()
    db.add(Applicant(full_name="Ayşe", department_id=dept["id"]))
    db.commit()
    make_patent(db, dept["id"])
    detail = client.delete(f"{URL}/{dept['id']}").json()["detail"]
    assert "patent" in detail and "başvuru sahibi" in detail


def test_delete_succeeds_without_links_and_other_departments_links_do_not_block(client, db):
    linked = post(client, "Bağlı").json()
    free = post(client, "Serbest").json()
    make_patent(db, linked["id"])
    assert client.delete(f"{URL}/{free['id']}").status_code == 204
    assert client.get(f"{URL}/{free['id']}").status_code == 404
    assert names(client) == ["Bağlı"]
    assert db.query(Department).filter_by(name="Serbest").count() == 0  # kalıcı silindi


# --- 422 ---

@pytest.mark.parametrize("body", [{"name": ""}, {"name": "   "}, {"name": "A", "id": 5}, {"name": "A", "created_at": "x"}, {}, {"name": 5}])
def test_invalid_body_422(client, body):
    assert client.post(URL, json=body).status_code == 422
    assert client.put(f"{URL}/1", json=body).status_code == 422


def test_name_length_boundary(client):
    assert post(client, "a" * 200).status_code == 201
    assert post(client, "b" * 201).status_code == 422
    assert client.get(f"{URL}/abc").status_code == 422


# --- servis: UNIQUE / FK yarış emniyeti ---

def test_service_unique_race_becomes_conflict_and_session_stays_usable(db, monkeypatch):
    monkeypatch.setattr(service, "name_taken", lambda *a, **k: False)  # normalize kontrolünü atlat
    service.create_department(db, DepartmentIn(name="Peyzaj"))
    with pytest.raises(ConflictError, match="zaten var"):
        service.create_department(db, DepartmentIn(name="Peyzaj"))  # ham UNIQUE ihlali
    assert [d.name for d in service.list_departments(db)] == ["Peyzaj"]  # rollback sonrası oturum çalışır
    other = service.create_department(db, DepartmentIn(name="Başka"))
    with pytest.raises(ConflictError):
        service.update_department(db, other.id, DepartmentIn(name="Peyzaj"))
    assert service.get_department(db, other.id).name == "Başka"


def test_service_delete_fk_race_becomes_conflict(db, monkeypatch):
    dept = service.create_department(db, DepartmentIn(name="Peyzaj"))
    make_patent(db, dept.id)
    monkeypatch.setattr(service, "_blocking_reasons", lambda *a, **k: [])  # ön kontrolü atlat
    with pytest.raises(ConflictError, match="başka kayıtlarca"):
        service.delete_department(db, dept.id)
    assert service.get_department(db, dept.id).name == "Peyzaj"


def test_service_errors_are_http_free(db):
    with pytest.raises(NotFoundError):
        service.get_department(db, 123)
    assert not hasattr(NotFoundError, "status_code") and not hasattr(ConflictError, "status_code")


# --- başlıklar ve gerçek DB'ye dokunmama ---

def test_frame_ancestors_on_all_department_responses(client, db):
    dept = post(client, "Peyzaj").json()
    make_patent(db, dept["id"])
    responses = [
        post(client, "Yeni"),                                   # 201
        post(client, "peyzaj"),                                 # 409 mükerrer
        client.delete(f"{URL}/{dept['id']}"),                   # 409 silme engeli
        client.get(f"{URL}/999"),                               # 404
        client.post(URL, json={"name": ""}),                    # 422
        client.get(URL),                                        # 200
        client.delete(f"{URL}/{post(client, 'Silinecek').json()['id']}"),  # 204
    ]
    assert [r.status_code for r in responses] == [201, 409, 409, 404, 422, 200, 204]
    for r in responses:
        assert r.headers["content-security-policy"] == "frame-ancestors 'self'"
        assert "x-frame-options" not in r.headers


def test_domain_error_response_shape_is_detail_only(client):
    post(client, "A")
    r = post(client, "a")
    assert r.status_code == 409 and list(r.json()) == ["detail"]
    assert r.headers["content-type"].startswith("application/json")


def test_openapi_documents_department_errors(client):
    spec = client.get("/openapi.json").json()["paths"]
    assert "409" in spec["/api/departments"]["post"]["responses"]
    assert {"404", "409"} <= set(spec["/api/departments/{item_id}"]["delete"]["responses"])
    assert "201" in spec["/api/departments"]["post"]["responses"]
    assert "204" in spec["/api/departments/{item_id}"]["delete"]["responses"]


def test_tests_never_touch_real_database_file(client):
    existed = database.DB_PATH.exists()
    post(client, "X")
    assert database.DB_PATH.exists() == existed
