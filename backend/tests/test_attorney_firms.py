import pytest

URL = "/api/attorney_firms"


def post(client, name, **extra):
    return client.post(URL, json={"name": name, **extra})


def test_crud_happy_path(client):
    r = post(client, "Destek Patent", contact_info="  0312 000 00 00 ")
    assert r.status_code == 201
    body = r.json()
    assert set(body) == {"id", "name", "contact_info", "tax_no", "title", "email", "is_active", "created_at", "updated_at"}
    assert body["contact_info"] == "0312 000 00 00"
    firm_id = body["id"]
    assert client.get(f"{URL}/{firm_id}").json()["name"] == "Destek Patent"
    r = client.put(f"{URL}/{firm_id}", json={"name": "Simaj", "contact_info": None, "is_active": False})
    assert r.status_code == 200
    assert (r.json()["name"], r.json()["contact_info"], r.json()["is_active"]) == ("Simaj", None, False)
    assert client.delete(f"{URL}/{firm_id}").status_code == 204
    assert client.get(f"{URL}/{firm_id}").status_code == 404


def test_is_active_defaults_to_true_and_list_includes_inactive(client):
    assert post(client, "Aktif").json()["is_active"] is True
    post(client, "Pasif", is_active=False)
    assert [(f["name"], f["is_active"]) for f in client.get(URL).json()] == [("Aktif", True), ("Pasif", False)]


def test_list_sorted_by_turkish_alphabet(client):
    for name in ["Zeta Patent", "Çözüm Patent", "Simaj", "Şahin Vekillik", "İz Patent", "Işık Patent"]:
        post(client, name)
    assert [f["name"] for f in client.get(URL).json()] == [
        "Çözüm Patent", "Işık Patent", "İz Patent", "Simaj", "Şahin Vekillik", "Zeta Patent",
    ]


@pytest.mark.parametrize("first, second", [("Destek Patent", "DESTEK   patent"), ("IŞIK Patent", "ışık patent")])
def test_normalized_duplicate_409_on_post_and_put(client, first, second):
    assert post(client, first).status_code == 201
    r = post(client, second)
    assert r.status_code == 409 and r.json() == {"detail": "Bu adla bir vekil firma zaten var."}
    other = post(client, "Başka Firma").json()
    assert client.put(f"{URL}/{other['id']}", json={"name": second}).status_code == 409


def test_put_with_own_name_is_ok(client):
    firm = post(client, "Destek Patent").json()
    assert client.put(f"{URL}/{firm['id']}", json={"name": "DESTEK PATENT"}).status_code == 200


def test_not_found(client):
    for r in (client.get(f"{URL}/999"), client.put(f"{URL}/999", json={"name": "X"}), client.delete(f"{URL}/999")):
        assert r.status_code == 404 and r.json() == {"detail": "Vekil firma bulunamadı."}


@pytest.mark.parametrize("body", [{"name": ""}, {"name": "A", "id": 1}, {"name": "a" * 201}, {"name": "A", "is_active": "x"}])
def test_invalid_body_422(client, body):
    assert client.post(URL, json=body).status_code == 422


def test_delete_with_active_linked_patent_is_409(client, make_patent):
    firm = post(client, "Bağlı").json()
    make_patent(attorney_firm_id=firm["id"])
    r = client.delete(f"{URL}/{firm['id']}")
    assert r.status_code == 409 and r.json() == {"detail": "Bu kayıt 1 aktif patentte kullanılıyor, silinemez."}
    assert client.get(f"{URL}/{firm['id']}").status_code == 200


def test_new_fields_trimmed_empty_to_none_and_validated(client):
    r = post(client, "Yeni", tax_no=" 1234567890 ", title="  Yeni Patent Ltd.  ", email=" info@yeni.com.tr ")
    assert r.status_code == 201
    assert (r.json()["tax_no"], r.json()["title"], r.json()["email"]) == ("1234567890", "Yeni Patent Ltd.", "info@yeni.com.tr")
    r = post(client, "Boş", tax_no="  ", title="", email=" ")
    assert (r.json()["tax_no"], r.json()["title"], r.json()["email"]) == (None, None, None)
    assert post(client, "Onbir", tax_no="12345678901").status_code == 201
    for bad in ("123456789", "123456789012", "12345abc90", "١٢٣٤٥٦٧٨٩٠"):  # kısa, uzun, harf, Arap-Hint rakamı
        r = post(client, f"V{bad}", tax_no=bad)
        assert r.status_code == 422 and r.json() == {"detail": "Vergi no 10 veya 11 haneli rakam olmalı."}, bad
    for bad in ("a", "a@b", "a@@b.com", "@b.com", "a@b.", "a@.com", "a b@c.com"):
        r = post(client, f"E{bad}", email=bad)
        assert r.status_code == 422 and r.json() == {"detail": "Geçerli bir e-posta adresi girin."}, bad
    other = client.get(URL).json()[0]
    r = client.put(f"{URL}/{other['id']}", json={"name": other["name"], "tax_no": "abc"})
    assert r.status_code == 422  # PUT'ta da doğrulanır
