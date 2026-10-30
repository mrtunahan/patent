from datetime import date
from io import BytesIO

from openpyxl import load_workbook

from app.models import Applicant, Department, FsmhType, PatentPartner

HEADERS = ["No", "Buluş Başlığı", "Başvuru Sahibi", "Bölüm / Birim", "FSMH Türü", "Vekil Firma",
           "Ortaklar & Oranları", "Başvuru Tarihi", "Notlar / Açıklama"]


def add(db, make_patent, title, notes=None, **links):
    patent = make_patent(**links)
    patent.title, patent.notes = title, notes
    db.commit()
    return patent


def rows(client, **params):
    r = client.get("/api/patents/export", params=params)
    assert r.status_code == 200
    ws = load_workbook(BytesIO(r.content)).active
    return r, [[c.value for c in row] for row in ws.iter_rows()]


def test_export_headers_order_dates_and_attachment_name(client, db, make_patent):
    mk = lambda title, notes=None, **kw: add(db, make_patent, title, notes, **kw)  # noqa: E731
    dept = Department(name="Gıda")
    db.add(dept)
    db.flush()
    mk("İkinci", "not", department_id=dept.id, application_date=date(2024, 3, 5))
    p = mk("Birinci")
    p.partners = [PatentPartner(partner_name="A Üni."), PatentPartner(partner_name="B Üni.")]
    db.commit()
    r, data = rows(client, sort_by="title")
    assert r.headers["content-disposition"] == f'attachment; filename="patent-takip-{date.today().isoformat()}.xlsx"'
    assert data[0] == HEADERS
    assert [row[:2] for row in data[1:]] == [[1, "Birinci"], [2, "İkinci"]]  # Türkçe sıralama, No 1'den
    assert data[1][6] == "A Üni., B Üni." and data[1][7] is None
    assert data[2][3] == "Gıda" and data[2][7].date() == date(2024, 3, 5) and data[2][8] == "not"
    ws = load_workbook(BytesIO(client.get("/api/patents/export").content)).active
    assert ws.freeze_panes == "A2" and ws["A1"].font.bold and ws["H3"].number_format == "DD.MM.YYYY"


def test_export_applies_filters_without_paging_and_skips_deleted(client, db, make_patent):
    db.add(Applicant(full_name="İlk Kişi"))  # make_patent varsayılanı bu olur
    other = Applicant(full_name="Başka Kişi")
    db.add(other)
    db.commit()
    for i in range(30):
        add(db, make_patent, f"Buluş {i}")
    add(db, make_patent, "Silinmiş", deleted=True)
    add(db, make_patent, "Hedef", applicant_id=other.id)
    assert len(rows(client)[1]) == 1 + 31  # sayfalama yok (30'dan fazla), silinmiş yok
    _, data = rows(client, applicant_id=other.id)
    assert [row[1] for row in data[1:]] == ["Hedef"]
    _, data = rows(client, q="zzz")
    assert data == [HEADERS]  # boş sonuçta da başlık satırı
    assert client.get("/api/patents/export", params={"page": 2}).status_code == 422


def test_export_never_writes_formulas(client, db, make_patent):
    add(db, make_patent, "=1+1", "@SUM(A1)")
    add(db, make_patent, "-5+x", "+cmd")
    r = client.get("/api/patents/export")
    ws = load_workbook(BytesIO(r.content)).active
    for ref in ("B2", "I2", "B3", "I3"):
        assert ws[ref].data_type == "s", ref
    assert ws["B2"].value == "=1+1" and ws["I2"].value == "@SUM(A1)"
