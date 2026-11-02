import pytest

URL = "/api/patents"


@pytest.fixture
def base(client):
    return {
        "title": "Tuz Lambası",
        "applicant_id": client.post("/api/applicants", json={"full_name": "Ayşe"}).json()["id"],
        "fsmh_type_id": client.post("/api/fsmh_types", json={"name": "Patent"}).json()["id"],
    }


def test_status_and_registration_date_roundtrip_and_empty_status_is_none(client, base):
    r = client.post(URL, json={**base, "application_date": "2024-01-10", "registration_date": "2024-01-10", "status": "Tescillendi"})
    assert r.status_code == 201
    got = r.json()
    assert (got["registration_date"], got["status"]) == ("2024-01-10", "Tescillendi")  # eşit tarih geçerli
    put = client.put(f"{URL}/{got['id']}", json={**base, "status": "", "registration_date": None})
    assert put.status_code == 200 and (put.json()["status"], put.json()["registration_date"]) == (None, None)
    assert client.get(f"{URL}/{got['id']}").json()["status"] is None
    for ok in ("Süreç Devam Ediyor", "Reddedildi"):
        assert client.put(f"{URL}/{got['id']}", json={**base, "status": ok}).json()["status"] == ok


def test_invalid_status_422_and_registration_before_application_422(client, base):
    assert client.post(URL, json={**base, "status": "Bekliyor"}).status_code == 422
    r = client.post(URL, json={**base, "application_date": "2024-02-01", "registration_date": "2024-01-31"})
    assert r.status_code == 422 and r.json() == {"detail": "Tescil tarihi başvuru tarihinden önce olamaz."}
    ok = client.post(URL, json={**base, "registration_date": "2020-01-01"})  # başvuru tarihi boşsa kontrol yok
    assert ok.status_code == 201
    pid = ok.json()["id"]
    bad = client.put(f"{URL}/{pid}", json={**base, "application_date": "2021-01-01", "registration_date": "2020-01-01"})
    assert bad.status_code == 422 and bad.json()["detail"] == "Tescil tarihi başvuru tarihinden önce olamaz."


def test_duplicate_check_ignores_registration_date_and_status(client, base):
    assert client.post(URL, json={**base, "status": "Reddedildi"}).status_code == 201
    r = client.post(URL, json={**base, "registration_date": "2025-05-05", "status": "Tescillendi"})
    assert r.status_code == 409 and r.json()["duplicate"] is True
