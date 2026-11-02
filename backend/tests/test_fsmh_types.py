from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

from conftest import build_client
from app.database import create_db_engine

URL = "/api/fsmh_types"
ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"


def post(client, name, sort_order=None):
    body = {"name": name} if sort_order is None else {"name": name, "sort_order": sort_order}
    return client.post(URL, json=body)


def test_crud_happy_path(client):
    r = post(client, "Endüstriyel Tasarım", 7)
    assert r.status_code == 201
    body = r.json()
    assert set(body) == {"id", "name", "sort_order", "created_at", "updated_at"}
    type_id = body["id"]
    assert client.get(f"{URL}/{type_id}").json()["sort_order"] == 7
    r = client.put(f"{URL}/{type_id}", json={"name": "Coğrafi İşaret", "sort_order": -3})
    assert r.status_code == 200
    assert (r.json()["name"], r.json()["sort_order"]) == ("Coğrafi İşaret", -3)
    assert client.delete(f"{URL}/{type_id}").status_code == 204
    assert client.get(f"{URL}/{type_id}").status_code == 404


def test_sort_order_defaults_to_zero_and_name_trimmed(client):
    r = post(client, "  Faydalı   Model  ")
    assert r.json()["name"] == "Faydalı   Model" and r.json()["sort_order"] == 0


def test_list_sorted_by_sort_order_then_turkish_name(client):
    post(client, "Zeta", 1)
    post(client, "Çiçek", 1)
    post(client, "Ankara", 1)
    post(client, "Alt", -5)
    post(client, "İzmir", 1)
    assert [t["name"] for t in client.get(URL).json()] == ["Alt", "Ankara", "Çiçek", "İzmir", "Zeta"]


def test_seeded_types_listed_in_order_via_migration(tmp_path):
    engine = create_db_engine(tmp_path / "migrated.db")
    cfg = Config(str(ALEMBIC_INI))
    with engine.begin() as conn:
        cfg.attributes["connection"] = conn
        command.upgrade(cfg, "head")  # create_all değil: Alembic seed'i
    listed = build_client(engine).get(URL).json()
    assert [(t["name"], t["sort_order"]) for t in listed] == [
        ("Patent", 1), ("Faydalı Model", 2), ("Tasarım Tescili", 3), ("Marka", 4), ("Telif Hakkı", 5),
    ]
    engine.dispose()


@pytest.mark.parametrize(
    "first, second",
    [("Faydalı Model", "FAYDALI  model"), ("Tasarım Tescili", "TASARIM TESCİLİ")],
)
def test_normalized_duplicate_409_on_post_and_put(client, first, second):
    assert post(client, first).status_code == 201
    r = post(client, second)
    assert r.status_code == 409
    assert r.json() == {"detail": "Bu adla bir FSMH türü zaten var."}
    other = post(client, "Başka Tür").json()
    assert client.put(f"{URL}/{other['id']}", json={"name": second}).status_code == 409


def test_put_with_own_name_is_ok(client):
    t = post(client, "Faydalı Model", 2).json()
    r = client.put(f"{URL}/{t['id']}", json={"name": "FAYDALI MODEL", "sort_order": 5})
    assert r.status_code == 200 and r.json()["name"] == "FAYDALI MODEL"


def test_not_found(client):
    for r in (client.get(f"{URL}/999"), client.put(f"{URL}/999", json={"name": "X"}), client.delete(f"{URL}/999")):
        assert r.status_code == 404
        assert r.json() == {"detail": "Tür bulunamadı."}


@pytest.mark.parametrize(
    "body",
    [{"name": ""}, {"name": "A", "id": 3}, {"name": "a" * 101}, {"name": "A", "sort_order": "abc"},
     {"name": "A", "sort_order": 2**31}, {"name": "A", "sort_order": 10**30}],  # taşma 500 değil 422
)
def test_invalid_body_422(client, body):
    assert client.post(URL, json=body).status_code == 422


def test_delete_without_links_is_204(client):
    t = post(client, "Serbest").json()
    assert client.delete(f"{URL}/{t['id']}").status_code == 204


def test_delete_with_active_linked_patent_is_409(client, make_patent):
    t = post(client, "Bağlı").json()
    make_patent(fsmh_type_id=t["id"])
    r = client.delete(f"{URL}/{t['id']}")
    assert r.status_code == 409 and r.json() == {"detail": "Bu kayıt 1 aktif patentte kullanılıyor, silinemez."}
    assert client.get(f"{URL}/{t['id']}").status_code == 200
