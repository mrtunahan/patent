from app.models import Applicant, AttorneyFirm, Department, PatentPartner


def add(db, make_patent, title, partners=(), deleted=False, **links):
    patent = make_patent(deleted=deleted, **links)
    patent.title = title
    patent.partners = [PatentPartner(partner_name=name) for name in partners]
    db.commit()
    return patent


def test_partners_group_by_normalized_name_first_spelling_and_skip_deleted(client, db, make_patent):
    a = add(db, make_patent, "B Buluş", ["Çankırı Karatekin Üni.", "Işık Üni."])
    b = add(db, make_patent, "A Buluş", ["ÇANKIRI  karatekin üni.", "Ankara Üni."])
    add(db, make_patent, "Silinmiş", ["Ankara Üni.", "Sadece Silinmişte"], deleted=True)
    got = client.get("/api/partners").json()
    assert [p["name"] for p in got] == ["Ankara Üni.", "Çankırı Karatekin Üni.", "Işık Üni."]  # Türkçe sıra; silinmişin ortağı yok
    ck = got[1]
    assert ck["patent_count"] == 2 and [p["id"] for p in ck["patents"]] == [a.id, b.id]
    assert ck["patents"][0] == {
        "id": a.id, "title": "B Buluş", "fsmh_type_name": "Patent", "status": None,
        "application_date": None, "registration_date": None,
    }
    assert got[0]["patent_count"] == 1  # silinmiş patent sayılmaz


def test_departments_summary_counts_active_only_and_includes_zero(client, db, make_patent):
    db.add_all([Department(name="Peyzaj"), Department(name="Gıda"), Department(name="Boş")])
    db.commit()
    ids = {d.name: d.id for d in db.query(Department)}
    p = add(db, make_patent, "Bir", department_id=ids["Peyzaj"])
    add(db, make_patent, "Silinmiş", department_id=ids["Peyzaj"], deleted=True)
    add(db, make_patent, "Bölümsüz")
    got = client.get("/api/departments/summary").json()
    assert [(d["name"], d["patent_count"]) for d in got] == [("Boş", 0), ("Gıda", 0), ("Peyzaj", 1)]
    assert [(x["id"], x["title"]) for x in got[2]["patents"]] == [(p.id, "Bir")] and got[0]["patents"] == []


def test_attorney_firms_summary_counts_and_zero_listed(client, db, make_patent):
    db.add_all([AttorneyFirm(name="Simaj"), AttorneyFirm(name="Grup Ofis")])
    db.add(Applicant(full_name="Varsayılan"))
    db.commit()
    simaj = db.query(AttorneyFirm).filter_by(name="Simaj").one()
    for title in ("Y", "X"):
        add(db, make_patent, title, attorney_firm_id=simaj.id)
    got = client.get("/api/attorney_firms/summary").json()
    assert [(f["name"], f["patent_count"]) for f in got] == [("Grup Ofis", 0), ("Simaj", 2)]
    assert [p["title"] for p in got[1]["patents"]] == ["Y", "X"]  # id sırası
    assert client.get("/api/attorney_firms/1").status_code in (200, 404)  # /summary, /{id} ile çakışmaz


def test_applicants_summary_counts_active_only_zero_included_and_sorted(client, db, make_patent):
    db.add_all([Applicant(full_name="Zeynep"), Applicant(full_name="Çağla"), Applicant(full_name="Ali")])
    db.commit()
    ids = {a.full_name: a.id for a in db.query(Applicant)}
    p1 = add(db, make_patent, "B", applicant_id=ids["Çağla"])
    p2 = add(db, make_patent, "A", applicant_id=ids["Çağla"])
    add(db, make_patent, "Silinmiş", applicant_id=ids["Çağla"], deleted=True)
    got = client.get("/api/applicants/summary").json()
    assert [(a["full_name"], a["patent_count"]) for a in got] == [("Ali", 0), ("Çağla", 2), ("Zeynep", 0)]
    assert [(x["id"], x["title"]) for x in got[1]["patents"]] == [(p1.id, "B"), (p2.id, "A")]
    assert got[0]["patents"] == [] and set(got[0]) == {"id", "full_name", "patent_count", "patents"}
    assert client.get(f"/api/applicants/{ids['Ali']}").status_code == 200  # /summary, /{id} ile çakışmaz


def test_summary_patents_carry_type_status_and_dates_on_all_endpoints(client, db, make_patent):
    from datetime import date

    dept = Department(name="Gıda")
    firm = AttorneyFirm(name="Simaj")
    db.add_all([dept, firm])
    db.commit()
    p = add(db, make_patent, "Dolu", ["Ortak"], department_id=dept.id, attorney_firm_id=firm.id,
            application_date=date(2024, 3, 5), registration_date=date(2025, 1, 2), status="Tescillendi")
    expected = {
        "id": p.id, "title": "Dolu", "fsmh_type_name": "Patent", "status": "Tescillendi",
        "application_date": "2024-03-05", "registration_date": "2025-01-02",
    }
    for url in ("/api/partners", "/api/departments/summary", "/api/attorney_firms/summary", "/api/applicants/summary"):
        rows = [r for r in client.get(url).json() if r["patents"]]
        assert rows[0]["patents"] == [expected], url
