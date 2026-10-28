import pytest
from sqlalchemy import event

URL = "/api/patents"


@pytest.fixture
def world(client):
    """İki başvuru sahibi, iki bölüm, bir vekil firma; 'Patent' ve 'Marka' türleri."""
    def make(path, body):
        return client.post(path, json=body).json()["id"]

    return {
        "ayse": make("/api/applicants", {"full_name": "Ayşe Yılmaz"}),
        "veli": make("/api/applicants", {"full_name": "Veli Demir"}),
        "peyzaj": make("/api/departments", {"name": "Peyzaj Mimarlığı"}),
        "mekatronik": make("/api/departments", {"name": "Mekatronik"}),
        "firma": make("/api/attorney_firms", {"name": "Destek Patent"}),
        "patent": make("/api/fsmh_types", {"name": "Patent"}),
        "marka": make("/api/fsmh_types", {"name": "Marka"}),
    }


def add(client, world, title, **over):
    payload = {"title": title, "applicant_id": world["ayse"], "fsmh_type_id": world["patent"], **over}
    r = client.post(f"{URL}?confirm_duplicate=true", json=payload)
    assert r.status_code == 201, r.text
    return r.json()["id"]


def listing(client, **params):
    r = client.get(URL, params=params)
    assert r.status_code == 200, r.text
    return r.json()


def titles(client, **params):
    return [p["title"] for p in listing(client, **params)["items"]]


def test_empty_list_envelope(client):
    assert listing(client) == {"items": [], "total": 0, "page": 1, "page_size": 25}


def test_default_order_is_id_ascending_and_soft_deleted_are_hidden(client, world):
    a = add(client, world, "Birinci")
    b = add(client, world, "İkinci")
    c = add(client, world, "Üçüncü")
    assert client.delete(f"{URL}/{b}").status_code == 204
    data = listing(client)
    assert [p["id"] for p in data["items"]] == [a, c]
    assert data["total"] == 2
    item = data["items"][0]  # PatentRead biçimi (iç içe), deleted_at yok
    assert item["applicant"]["full_name"] == "Ayşe Yılmaz" and item["partners"] == [] and "deleted_at" not in item


def test_pagination(client, world):
    for i in range(1, 6):
        add(client, world, f"Patent {i}")
    first = listing(client, page=1, page_size=2)
    assert (first["total"], first["page"], first["page_size"]) == (5, 1, 2)
    assert [p["title"] for p in first["items"]] == ["Patent 1", "Patent 2"]
    assert titles(client, page=3, page_size=2) == ["Patent 5"]
    beyond = listing(client, page=4, page_size=2)
    assert beyond["items"] == [] and beyond["total"] == 5 and beyond["page"] == 4
    assert client.get(URL, params={"page_size": 101}).status_code == 422


@pytest.mark.parametrize(
    "param, key, expected",
    [
        ("applicant_id", "veli", ["Veli'nin"]),
        ("department_id", "mekatronik", ["Mekatronikçi"]),
        ("fsmh_type_id", "marka", ["Markalı"]),
        ("attorney_firm_id", "firma", ["Vekilli"]),
    ],
)
def test_id_filters(client, world, param, key, expected):
    add(client, world, "Hiçbiri")
    add(client, world, "Veli'nin", applicant_id=world["veli"])
    add(client, world, "Mekatronikçi", department_id=world["mekatronik"])
    add(client, world, "Markalı", fsmh_type_id=world["marka"])
    add(client, world, "Vekilli", attorney_firm_id=world["firma"])
    data = listing(client, **{param: world[key]})
    assert [p["title"] for p in data["items"]] == expected and data["total"] == 1


def test_date_range_is_inclusive_and_empty_dates_are_dropped(client, world):
    add(client, world, "Ocak", application_date="2026-01-01")
    add(client, world, "Şubat", application_date="2026-02-01")
    add(client, world, "Mart", application_date="2026-03-01")
    add(client, world, "Tarihsiz")
    assert titles(client) == ["Ocak", "Şubat", "Mart", "Tarihsiz"]  # filtre yoksa tarihsiz de gelir
    assert titles(client, date_from="2026-02-01") == ["Şubat", "Mart"]
    assert titles(client, date_to="2026-02-01") == ["Ocak", "Şubat"]
    assert titles(client, date_from="2026-02-01", date_to="2026-02-01") == ["Şubat"]


def test_has_attorney_true_and_false(client, world):
    add(client, world, "Vekilli", attorney_firm_id=world["firma"])
    add(client, world, "Vekilsiz")
    assert titles(client, has_attorney="true") == ["Vekilli"]
    assert titles(client, has_attorney="false") == ["Vekilsiz"]
    assert titles(client) == ["Vekilli", "Vekilsiz"]


def test_q_searches_title_applicant_partner_and_notes(client, world):
    add(client, world, "Tuz Lambası")
    add(client, world, "Başka", partners=["Gazi Üniversitesi"])
    add(client, world, "Üçüncü", notes="Ödeme yapılması gerekiyor.")
    add(client, world, "Dördüncü", applicant_id=world["veli"])
    assert titles(client, q="lambası") == ["Tuz Lambası"]          # başlık
    assert titles(client, q="gazi üni") == ["Başka"]                # ortak
    assert titles(client, q="ödeme") == ["Üçüncü"]                  # not
    assert titles(client, q="demir") == ["Dördüncü"]                # başvuru sahibi
    assert titles(client, q="  TUZ   ") == ["Tuz Lambası"]          # kırpma + büyük/küçük
    assert len(titles(client, q="   ")) == 4                        # boş q: filtre yok


def test_q_is_turkish_case_insensitive_and_does_not_fold_accents(client, world):
    add(client, world, "Şabanözü Projesi")
    add(client, world, "Işık Sistemi")
    add(client, world, "Saban Aleti")
    assert titles(client, q="ŞABANÖZÜ") == ["Şabanözü Projesi"]
    assert titles(client, q="şabanözü") == ["Şabanözü Projesi"]
    assert titles(client, q="IŞIK") == ["Işık Sistemi"]
    assert titles(client, q="ışık") == ["Işık Sistemi"]
    assert titles(client, q="isik") == []                      # I->ı, aksan katlanmaz
    assert titles(client, q="şaban") == ["Şabanözü Projesi"]   # 'saban' kaydını getirmez
    assert titles(client, q="saban") == ["Saban Aleti"]        # 'şaban' kaydını getirmez


def test_sort_by_title_uses_turkish_alphabet(client, world):
    for t in ["Zil", "Şişe", "Ada", "İp", "Çiçek"]:
        add(client, world, t)
    assert titles(client, sort_by="title") == ["Ada", "Çiçek", "İp", "Şişe", "Zil"]
    assert titles(client, sort_by="title", sort_dir="desc") == ["Zil", "Şişe", "İp", "Çiçek", "Ada"]


def test_sort_by_application_date_puts_none_last_in_both_directions(client, world):
    add(client, world, "Tarihsiz 1")
    add(client, world, "Mart", application_date="2026-03-01")
    add(client, world, "Ocak", application_date="2026-01-01")
    add(client, world, "Tarihsiz 2")
    assert titles(client, sort_by="application_date") == ["Ocak", "Mart", "Tarihsiz 1", "Tarihsiz 2"]
    assert titles(client, sort_by="application_date", sort_dir="desc") == ["Mart", "Ocak", "Tarihsiz 1", "Tarihsiz 2"]


def test_ties_are_broken_by_id_ascending_even_when_descending(client, world):
    add(client, world, "A", application_date="2026-01-01")
    add(client, world, "B", application_date="2026-01-01")
    add(client, world, "C", application_date="2026-02-01")
    assert titles(client, sort_by="application_date", sort_dir="desc") == ["C", "A", "B"]
    assert titles(client, sort_by="id", sort_dir="desc") == ["C", "B", "A"]


def test_sort_by_related_names_and_missing_related_go_last(client, world):
    add(client, world, "P1", applicant_id=world["veli"], department_id=world["peyzaj"], attorney_firm_id=world["firma"])
    add(client, world, "P2", applicant_id=world["ayse"], department_id=world["mekatronik"])
    add(client, world, "P3")  # bölümsüz, vekilsiz
    assert titles(client, sort_by="applicant") == ["P2", "P3", "P1"]               # Ayşe, Ayşe, Veli
    assert titles(client, sort_by="department") == ["P2", "P1", "P3"]              # Mekatronik, Peyzaj, yok
    assert titles(client, sort_by="department", sort_dir="desc") == ["P1", "P2", "P3"]
    assert titles(client, sort_by="attorney_firm", sort_dir="desc") == ["P1", "P2", "P3"]
    assert titles(client, sort_by="fsmh_type") == ["P1", "P2", "P3"]
    assert titles(client, sort_by="created_at", sort_dir="desc")[0] == "P3"


def test_q_filter_and_pagination_together_total_is_after_q(client, world):
    for i in range(1, 6):
        add(client, world, f"Lamba {i}", applicant_id=world["ayse"])
    add(client, world, "Lamba Veli", applicant_id=world["veli"])
    add(client, world, "Başka şey")
    data = listing(client, q="lamba", applicant_id=world["ayse"], page=2, page_size=2, sort_by="title")
    assert data["total"] == 5 and [p["title"] for p in data["items"]] == ["Lamba 3", "Lamba 4"]


def test_list_does_not_run_per_row_queries(client, world, engine):
    for i in range(12):
        add(client, world, f"P{i}", department_id=world["peyzaj"], attorney_firm_id=world["firma"],
            partners=[f"Ortak {i}"])
    statements = []
    event.listen(engine, "before_cursor_execute", lambda *a: statements.append(a[2]))
    data = listing(client, q="p", page_size=100)
    assert data["total"] == 12 and all(len(p["partners"]) == 1 for p in data["items"])
    assert len(statements) <= 3  # ana sorgu + ortaklar (selectinload); satır başına sorgu yok
