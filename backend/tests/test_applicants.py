import pytest

URL = "/api/applicants"


def post(client, full_name, **extra):
    return client.post(URL, json={"full_name": full_name, **extra})


def make_department(client, name="Peyzaj Mimarlığı"):
    return client.post("/api/departments", json={"name": name}).json()["id"]


def test_crud_happy_path(client):
    dept_id = make_department(client)
    r = post(client, "  Ayşe   Yılmaz ", department_id=dept_id, email=" ayse@example.com ")
    assert r.status_code == 201
    body = r.json()
    assert set(body) == {"id", "full_name", "department_id", "email", "is_active", "created_at", "updated_at"}
    assert (body["full_name"], body["email"], body["department_id"]) == ("Ayşe   Yılmaz", "ayse@example.com", dept_id)
    applicant_id = body["id"]
    assert client.get(f"{URL}/{applicant_id}").json()["full_name"] == "Ayşe   Yılmaz"
    r = client.put(f"{URL}/{applicant_id}", json={"full_name": "Ayşe Demir", "is_active": False})
    assert r.status_code == 200
    assert (r.json()["full_name"], r.json()["department_id"], r.json()["email"], r.json()["is_active"]) == (
        "Ayşe Demir", None, None, False,  # PUT tam değiştirme: verilmeyen alanlar varsayılana döner
    )
    assert client.delete(f"{URL}/{applicant_id}").status_code == 204
    assert client.get(f"{URL}/{applicant_id}").status_code == 404


def test_is_active_defaults_to_true_and_blank_email_becomes_null(client):
    body = post(client, "Ali Veli", email="   ").json()
    assert body["is_active"] is True and body["email"] is None


def test_list_sorted_by_turkish_alphabet(client):
    for name in ["Zeynep Kaya", "Çağla Er", "Ali Veli", "Şule Ak", "İbrahim Su", "Ilgaz Tan"]:
        post(client, name)
    assert [a["full_name"] for a in client.get(URL).json()] == [
        "Ali Veli", "Çağla Er", "Ilgaz Tan", "İbrahim Su", "Şule Ak", "Zeynep Kaya",
    ]


@pytest.mark.parametrize("first, second", [("Ayşe Yılmaz", "AYŞE   yılmaz"), ("Işıl Çelik", "IŞIL ÇELİK")])
def test_normalized_duplicate_409_on_post_and_put(client, first, second):
    assert post(client, first).status_code == 201
    r = post(client, second)
    assert r.status_code == 409 and r.json() == {"detail": "Bu adla bir başvuru sahibi zaten var."}
    other = post(client, "Başka Kişi").json()
    assert client.put(f"{URL}/{other['id']}", json={"full_name": second}).status_code == 409


def test_put_with_own_name_is_ok(client):
    applicant = post(client, "Ayşe Yılmaz").json()
    assert client.put(f"{URL}/{applicant['id']}", json={"full_name": "AYŞE YILMAZ"}).status_code == 200


def test_department_must_exist_422_with_field_name(client):
    expected = {"detail": "Bölüm bulunamadı (department_id)."}
    r = post(client, "Ali Veli", department_id=999)
    assert r.status_code == 422 and r.json() == expected
    assert client.get(URL).json() == []  # kayıt oluşmadı
    other = post(client, "Ayşe").json()
    r = client.put(f"{URL}/{other['id']}", json={"full_name": "Ayşe", "department_id": 999})
    assert r.status_code == 422 and r.json() == expected
    # geçerli department_id kabul
    dept_id = make_department(client)
    assert post(client, "Veli", department_id=dept_id).status_code == 201
    assert client.put(f"{URL}/{other['id']}", json={"full_name": "Ayşe", "department_id": dept_id}).status_code == 200


def test_not_found(client):
    for r in (client.get(f"{URL}/999"), client.put(f"{URL}/999", json={"full_name": "X"}), client.delete(f"{URL}/999")):
        assert r.status_code == 404 and r.json() == {"detail": "Başvuru sahibi bulunamadı."}


@pytest.mark.parametrize(
    "body",
    [{"full_name": ""}, {"full_name": "A", "id": 1}, {"full_name": "a" * 201}, {"full_name": "A", "email": "a" * 201},
     {"full_name": "A", "department_id": 10**30}],  # taşan id 500 değil 422
)
def test_invalid_body_422(client, body):
    assert client.post(URL, json=body).status_code == 422


def test_huge_path_id_is_422_not_500(client):
    for method in (client.get, client.delete):
        assert method(f"{URL}/{10**30}").status_code == 422
    assert client.get(f"/api/departments/{10**30}").status_code == 422


def test_delete_with_active_linked_patent_is_409(client, make_patent):
    applicant = post(client, "Bağlı Kişi").json()
    make_patent(applicant_id=applicant["id"])
    r = client.delete(f"{URL}/{applicant['id']}")
    assert r.status_code == 409 and r.json() == {"detail": "Bu kayıt 1 aktif patentte kullanılıyor, silinemez."}
    assert client.get(f"{URL}/{applicant['id']}").status_code == 200
