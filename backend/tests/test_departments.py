import pytest

URL = "/api/departments"
IN_USE = {"detail": "Bu kayıt başka kayıtlarca kullanıldığı için silinemez."}


def post(client, name):
    return client.post(URL, json={"name": name})


def test_crud_happy_path(client):
    r = post(client, "Peyzaj Mimarlığı")
    assert r.status_code == 201
    body = r.json()
    assert set(body) == {"id", "name", "created_at", "updated_at"}
    dept_id = body["id"]
    assert client.get(f"{URL}/{dept_id}").json()["name"] == "Peyzaj Mimarlığı"
    assert [d["id"] for d in client.get(URL).json()] == [dept_id]
    r = client.put(f"{URL}/{dept_id}", json={"name": "Peyzaj Mimarlığı Bölümü"})
    assert r.status_code == 200 and r.json()["name"] == "Peyzaj Mimarlığı Bölümü"
    assert client.delete(f"{URL}/{dept_id}").status_code == 204
    assert client.get(f"{URL}/{dept_id}").status_code == 404


def test_name_trimmed_inner_spaces_and_spelling_kept(client):
    assert post(client, "  ŞABANÖZÜ   MYO  ").json()["name"] == "ŞABANÖZÜ   MYO"


def test_list_sorted_by_turkish_alphabet(client):
    for name in ["Zonguldak MYO", "Çankırı Mühendislik", "Ankara", "Şabanözü MYO", "Sivas", "Ödemiş",
                 "Işık Meslek", "İzmir", "Ulus", "Üsküdar"]:
        post(client, name)
    assert [d["name"] for d in client.get(URL).json()] == [
        "Ankara", "Çankırı Mühendislik", "Işık Meslek", "İzmir", "Ödemiş",
        "Sivas", "Şabanözü MYO", "Ulus", "Üsküdar", "Zonguldak MYO",
    ]


@pytest.mark.parametrize(
    "first, second",
    [("Peyzaj Mimarlığı", "peyzaj  mimarlığı"), ("IŞIK", "ışık"), ("İstanbul", "istanbul")],
)
def test_normalized_duplicate_409_on_post_and_put(client, first, second):
    assert post(client, first).status_code == 201
    r = post(client, second)
    assert r.status_code == 409
    assert r.json() == {"detail": "Bu adla bir bölüm zaten var."}
    other = post(client, "Bilgisayar").json()
    assert client.put(f"{URL}/{other['id']}", json={"name": second}).status_code == 409
    assert client.get(f"{URL}/{other['id']}").json()["name"] == "Bilgisayar"


def test_put_with_own_name_is_ok(client):
    dept = post(client, "Peyzaj Mimarlığı").json()
    r = client.put(f"{URL}/{dept['id']}", json={"name": "PEYZAJ MİMARLIĞI"})
    assert r.status_code == 200 and r.json()["name"] == "PEYZAJ MİMARLIĞI"


def test_not_found(client):
    for r in (client.get(f"{URL}/999"), client.put(f"{URL}/999", json={"name": "X"}), client.delete(f"{URL}/999")):
        assert r.status_code == 404
        assert r.json() == {"detail": "Bölüm bulunamadı."}


@pytest.mark.parametrize("body", [{"name": ""}, {"name": "   "}, {"name": "A", "id": 5}, {"name": "a" * 201}, {}])
def test_invalid_body_422(client, body):
    assert client.post(URL, json=body).status_code == 422


def test_delete_without_links_is_204(client):
    dept = post(client, "Serbest").json()
    assert client.delete(f"{URL}/{dept['id']}").status_code == 204
    assert client.get(URL).json() == []


def test_delete_with_linked_patent_is_generic_409(client, make_patent):
    dept = post(client, "Bağlı").json()
    make_patent(department_id=dept["id"])
    r = client.delete(f"{URL}/{dept['id']}")
    assert r.status_code == 409 and r.json() == IN_USE
    assert client.get(f"{URL}/{dept['id']}").status_code == 200  # rollback: kayıt duruyor
