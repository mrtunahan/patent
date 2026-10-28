import time

import pytest

from app.models import Patent, PatentPartner

URL = "/api/patents"
DUPLICATE_BODY = {"duplicate": True, "detail": "Aynı başlık, başvuru sahibi ve tarihle kayıt var."}


@pytest.fixture
def ids(client):
    """Bağlanacak lookup kayıtları (API ile oluşturulur)."""
    return {
        "applicant_id": client.post("/api/applicants", json={"full_name": "Ayşe Yılmaz"}).json()["id"],
        "fsmh_type_id": client.post("/api/fsmh_types", json={"name": "Patent"}).json()["id"],
        "department_id": client.post("/api/departments", json={"name": "Peyzaj Mimarlığı"}).json()["id"],
        "attorney_firm_id": client.post("/api/attorney_firms", json={"name": "Destek Patent"}).json()["id"],
    }


def body(ids, **over):
    base = {"title": "Modüler Tuz Lambası", "applicant_id": ids["applicant_id"], "fsmh_type_id": ids["fsmh_type_id"]}
    return {**base, **over}


def test_create_happy_path_nested_read_and_get(client, ids):
    payload = body(
        ids, title="  Modüler   Tuz Lambası ", department_id=ids["department_id"],
        attorney_firm_id=ids["attorney_firm_id"], application_date="2026-03-05", notes=" Ödeme yapılacak ",
        partners=[" Ankara Üni. ", "Çankırı Karatekin Üni."],
    )
    r = client.post(URL, json=payload)
    assert r.status_code == 201
    got = r.json()
    assert got["title"] == "Modüler   Tuz Lambası" and got["notes"] == "Ödeme yapılacak"
    assert got["applicant"] == {"id": ids["applicant_id"], "full_name": "Ayşe Yılmaz"}
    assert got["department"] == {"id": ids["department_id"], "name": "Peyzaj Mimarlığı"}
    assert got["fsmh_type"] == {"id": ids["fsmh_type_id"], "name": "Patent"}
    assert got["attorney_firm"] == {"id": ids["attorney_firm_id"], "name": "Destek Patent"}
    assert got["partners"] == ["Ankara Üni.", "Çankırı Karatekin Üni."]  # id sırası, yazım aynen
    assert got["application_date"] == "2026-03-05"
    assert "deleted_at" not in got
    assert client.get(f"{URL}/{got['id']}").json() == got
    minimal = client.post(URL, json=body(ids, title="Başka")).json()
    assert minimal["department"] is None and minimal["attorney_firm"] is None
    assert minimal["partners"] == [] and minimal["application_date"] is None


def test_put_replaces_partners_and_bumps_updated_at(client, ids):
    created = client.post(URL, json=body(ids, partners=["Ankara Üni.", "Gazi Üni."])).json()
    time.sleep(0.01)
    r = client.put(f"{URL}/{created['id']}", json=body(ids, partners=["Hacettepe Üni."]))  # yalnızca ortaklar değişti
    assert r.status_code == 200
    assert r.json()["partners"] == ["Hacettepe Üni."]
    assert r.json()["updated_at"] > created["updated_at"]
    assert r.json()["created_at"] == created["created_at"]
    r = client.put(f"{URL}/{created['id']}", json=body(ids, title="Yeni Başlık"))  # PUT tam değiştirme
    assert r.json()["title"] == "Yeni Başlık" and r.json()["partners"] == []


def test_soft_delete_hides_record_but_keeps_row(client, ids, db):
    created = client.post(URL, json=body(ids, partners=["Ankara Üni."])).json()
    assert client.delete(f"{URL}/{created['id']}").status_code == 204
    for r in (client.get(f"{URL}/{created['id']}"), client.put(f"{URL}/{created['id']}", json=body(ids)),
              client.delete(f"{URL}/{created['id']}")):
        assert r.status_code == 404 and r.json() == {"detail": "Patent bulunamadı."}
    row = db.query(Patent).filter_by(id=created["id"]).one()
    assert row.deleted_at is not None  # satır veritabanında korunur
    assert db.query(PatentPartner).filter_by(patent_id=created["id"]).count() == 1


def test_not_found(client, ids):
    assert client.get(f"{URL}/999").status_code == 404
    assert client.put(f"{URL}/999", json=body(ids)).json() == {"detail": "Patent bulunamadı."}
    assert client.delete(f"{URL}/999").status_code == 404


@pytest.mark.parametrize(
    "mutate",
    [
        lambda b: b.pop("title"), lambda b: b.pop("applicant_id"), lambda b: b.pop("fsmh_type_id"),
        lambda b: b.update(id=5), lambda b: b.update(deleted_at="2026-01-01"), lambda b: b.update(title="   "),
        lambda b: b.update(partners=["A", "  "]), lambda b: b.update(application_date="05.03.2026"),
    ],
)
def test_invalid_body_422(client, ids, mutate):
    payload = body(ids)
    mutate(payload)
    assert client.post(URL, json=payload).status_code == 422


@pytest.mark.parametrize(
    "field, message",
    [
        ("applicant_id", "Başvuru sahibi bulunamadı (applicant_id)."),
        ("fsmh_type_id", "FSMH türü bulunamadı (fsmh_type_id)."),
        ("department_id", "Bölüm bulunamadı (department_id)."),
        ("attorney_firm_id", "Vekil firma bulunamadı (attorney_firm_id)."),
    ],
)
def test_missing_reference_is_422_with_field_name(client, ids, field, message):
    r = client.post(URL, json=body(ids, **{field: 9999}))
    assert r.status_code == 422 and r.json() == {"detail": message}
    created = client.post(URL, json=body(ids)).json()
    r = client.put(f"{URL}/{created['id']}", json=body(ids, **{field: 9999}))
    assert r.status_code == 422 and r.json() == {"detail": message}


def test_partner_name_duplicate_is_422_on_post_and_put(client, ids):
    dup = {"detail": "Aynı ortak adı birden fazla kez eklenemez."}
    r = client.post(URL, json=body(ids, partners=["Ankara Üni.", "ankara   üni."]))
    assert r.status_code == 422 and r.json() == dup
    assert client.post(URL, json=body(ids, partners=["ISPARTA Üni.", "ısparta üni."])).status_code == 422
    created = client.post(URL, json=body(ids, partners=["Gazi Üni."])).json()
    assert client.put(f"{URL}/{created['id']}", json=body(ids, partners=["ÇANKIRI", "Çankırı"])).json() == dup
    assert client.post(URL, json=body(ids, title="Üçüncü", partners=["Şu Üni.", "Su Üni."])).status_code == 201  # aksan katlanmaz


def test_duplicate_warning_409_then_confirm_saves(client, ids):
    first = client.post(URL, json=body(ids, application_date="2026-03-05")).json()
    again = body(ids, title="MODÜLER  tuz lambası", application_date="2026-03-05")  # normalize eşit
    r = client.post(URL, json=again)
    assert r.status_code == 409
    assert r.json() == {**DUPLICATE_BODY, "existing_ids": [first["id"]]}
    assert len(client.post(URL, json=again).json()["existing_ids"]) == 1  # hâlâ yalnızca ilk kayıt
    r = client.post(f"{URL}?confirm_duplicate=true", json=again)
    assert r.status_code == 201 and r.json()["id"] != first["id"]
    r = client.post(URL, json=again)  # artık iki kayıt var
    assert r.status_code == 409 and sorted(r.json()["existing_ids"]) == [first["id"], r.json()["existing_ids"][-1]]


def test_put_not_duplicate_of_itself_but_of_others(client, ids):
    a = client.post(URL, json=body(ids, title="A Başlığı")).json()
    b = client.post(URL, json=body(ids, title="B Başlığı")).json()
    assert client.put(f"{URL}/{a['id']}", json=body(ids, title="A Başlığı", notes="not")).status_code == 200
    r = client.put(f"{URL}/{b['id']}", json=body(ids, title="a başlığı"))
    assert r.status_code == 409 and r.json()["existing_ids"] == [a["id"]]
    assert client.put(f"{URL}/{b['id']}?confirm_duplicate=true", json=body(ids, title="a başlığı")).status_code == 200


def test_duplicate_rules_deleted_null_dates_and_other_keys(client, ids):
    first = client.post(URL, json=body(ids)).json()  # tarihsiz
    assert client.post(URL, json=body(ids)).status_code == 409  # NULL tarihli ikisi eşit sayılır
    assert client.post(URL, json=body(ids, application_date="2026-03-05")).status_code == 201  # farklı tarih
    other = client.post("/api/applicants", json={"full_name": "Veli Demir"}).json()["id"]
    assert client.post(URL, json=body(ids, applicant_id=other)).status_code == 201  # farklı başvuru sahibi
    assert client.delete(f"{URL}/{first['id']}").status_code == 204
    assert client.post(URL, json=body(ids)).status_code == 201  # silinmiş patent mükerrer sayılmaz


def test_future_date_and_inactive_references_accepted(client, ids):
    client.put(f"/api/applicants/{ids['applicant_id']}", json={"full_name": "Ayşe Yılmaz", "is_active": False})
    client.put(f"/api/attorney_firms/{ids['attorney_firm_id']}", json={"name": "Destek Patent", "is_active": False})
    r = client.post(URL, json=body(ids, application_date="2099-12-31", attorney_firm_id=ids["attorney_firm_id"]))
    assert r.status_code == 201 and r.json()["application_date"] == "2099-12-31"


def test_huge_patent_id_is_422_not_500(client, ids):
    for r in (client.get(f"{URL}/{10**30}"), client.delete(f"{URL}/{10**30}"),
              client.put(f"{URL}/{10**30}", json=body(ids))):
        assert r.status_code == 422
    assert client.post(URL, json=body(ids, applicant_id=10**30)).status_code == 422
