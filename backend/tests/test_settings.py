import pytest

URL = "/api/settings"


def test_get_empty_settings(client):
    r = client.get(URL)
    assert r.status_code == 200 and r.json() == {}


def test_put_adds_updates_and_keeps_unsent_keys(client):
    r = client.put(URL, json={"institution_name": "Çankırı Karatekin Üniversitesi", "default_page_size": "25"})
    assert r.status_code == 200
    assert r.json() == {"default_page_size": "25", "institution_name": "Çankırı Karatekin Üniversitesi"}
    r = client.put(URL, json={"default_page_size": "50"})  # kısmi: diğer anahtar korunur
    assert r.json() == {"default_page_size": "50", "institution_name": "Çankırı Karatekin Üniversitesi"}
    assert client.get(URL).json() == r.json()
    assert client.put(URL, json={}).json() == r.json()  # boş gövde: değişiklik yok


def test_values_are_trimmed_and_empty_string_is_valid(client):
    r = client.put(URL, json={" institution_name ": "  ÇAKÜ  ", "note": ""})
    assert r.json() == {"institution_name": "ÇAKÜ", "note": ""}


@pytest.mark.parametrize("body", [{"": "x"}, {"   ": "x"}, {"k": 5}, {"k": None}, {"a": "1", " a ": "2"}, {"k" * 101: "x"}, ["k"]])
def test_invalid_body_422(client, body):
    assert client.put(URL, json=body).status_code == 422
    assert client.get(URL).json() == {}  # hiçbir şey yazılmadı
