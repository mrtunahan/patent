import importlib.util
import sys
from datetime import datetime
from pathlib import Path

import openpyxl
import pytest

from app.models import Applicant, AttorneyFirm, Department, FsmhType, Patent, PatentPartner

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "excel_import.py"
spec = importlib.util.spec_from_file_location("excel_import", SCRIPT)
excel_import = importlib.util.module_from_spec(spec)
sys.modules["excel_import"] = excel_import  # dataclass çözümlemesi için yüklemeden önce kaydedilmeli
spec.loader.exec_module(excel_import)


@pytest.fixture
def seeded(db):
    names = ["Patent", "Faydalı Model", "Tasarım Tescili", "Marka"]
    db.add_all([FsmhType(name=n, sort_order=i) for i, n in enumerate(names, 1)])
    db.commit()
    return db


def make_xlsx(path, headers, rows):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Patent Takip"
    ws.append(headers)
    for r in rows:
        ws.append(r)
    wb.save(path)
    return path


def run(db, path, apply=True):
    return excel_import.import_rows(excel_import.read_sheet(path), db, apply)


def counts(db):
    return tuple(db.query(m).count() for m in (Patent, Applicant, Department, AttorneyFirm, PatentPartner))


HEADERS = ["No", "Başvuru Sahibi", "Bölüm", "FSMH Türü", "Kapsam", "Komisyon Onay Durumu", "Vekil Firma",
           "Ortaklar ve Oranları", "Başvuru Tarihi", "Mevcut Durum", "Masraf", "Notlar", "Buluş Başlığı"]


def row(no, applicant, dept, ftype, firm, partners, date, notes, title):
    return [no, applicant, dept, ftype, "Ulusal", "Kabul", firm, partners, date, "Reddedildi", None, notes, title]


def test_basic_import_maps_headers_by_name_and_skips_out_of_schema_columns(seeded, tmp_path):
    path = make_xlsx(tmp_path / "a.xlsx", HEADERS, [
        row(1, " Didar Üçüncüoğlu ", "Gıda Mühendisliği", "patent", None, "Çankırı Karatekin Üni.", datetime(2019, 2, 25), " Süreçler sona erdi. ", "Zeytin Ezmeli Cips"),
        row(2, "yadigar ordu", '"AYRILDI"', "Tasarım Tescili", "Simaj", "Ankara Üni.", None, None, "Sesli Maske"),
        row(3, "Didar Üçüncüoğlu", "GIDA MÜHENDİSLİĞİ", "Faydalı Model", None, None, None, None, "İkinci Buluş"),
        [4] + [None] * 12, [5] + [None] * 12,  # yalnızca "No" dolu satırlar
    ])
    report = run(seeded, path)
    assert (len(report.imported), len(report.skipped), report.empty_rows, report.read_rows) == (3, 0, [5, 6], 3)
    assert report.ignored_headers == ["No", "Kapsam", "Komisyon Onay Durumu", "Mevcut Durum", "Masraf"]
    assert counts(seeded)[:4] == (3, 2, 1, 1)  # 2 başvuru sahibi, 1 bölüm (Gıda), 1 vekil firma
    assert report.created_departments == ["Gıda Mühendisliği"]  # "GIDA MÜHENDİSLİĞİ" mevcut kayıtla eşlendi
    first = seeded.query(Patent).order_by(Patent.id).first()
    assert (first.title, first.notes, first.application_date.isoformat()) == ("Zeytin Ezmeli Cips", "Süreçler sona erdi.", "2019-02-25")
    assert first.fsmh_type.name == "Patent" and first.applicant.full_name == "Didar Üçüncüoğlu"
    assert first.applicant.department_id is None  # başvuru sahibinin varsayılan bölümü NULL kalır
    ayrildi = seeded.query(Patent).filter_by(title="Sesli Maske").one()
    assert ayrildi.department_id is None and ayrildi.attorney_firm.name == "Simaj"
    assert report.ayrildi_rows == [(3, "yadigar ordu")]
    assert [d.name for d in seeded.query(Department)] == ["Gıda Mühendisliği"]  # "AYRILDI" bölüm olmadı


def test_partner_splitting_ratios_and_duplicates():
    split = excel_import.split_partners
    assert split("Çankırı Karatekin Üni.") == ["Çankırı Karatekin Üni."]
    assert split("Ankara Üni. %60, Gazi Üni. (%40)") == ["Ankara Üni.", "Gazi Üni."]
    assert split("Ankara Üni. 60%; ankara   üni.\nHacettepe Üni./ ODTÜ , ") == ["Ankara Üni.", "Hacettepe Üni.", "ODTÜ"]
    assert split("A %33,5, B %66.5") == ["A", "B"]
    assert split("   ") == [] and split("%50") == []
    assert split("Işık Üni., IŞIK  üni.") == ["Işık Üni."]  # normalize_tr ile tekrar elenir


def test_date_formats(seeded, tmp_path):
    values = [datetime(2026, 3, 5, 0, 0), "05.03.2026", "5.3.2026", "2026-03-05", "31.02.2026", "yakında", None]
    rows = [row(i, "Ayşe", "Bölüm", "Patent", None, None, v, None, f"Buluş {i}") for i, v in enumerate(values, 1)]
    report = run(seeded, make_xlsx(tmp_path / "d.xlsx", HEADERS, rows))
    assert len(report.imported) == 7 and not report.skipped  # çözülemeyen tarih satırı atlamaz
    assert [r["application_date"] for r in report.imported] == ["2026-03-05"] * 4 + [None, None, None]
    assert report.unresolved_dates == [(6, "31.02.2026"), (7, "yakında")]
    assert report.undated_rows == 1  # gerçekten boş olan, çözülemeyenlerden ayrı sayılır


def test_second_run_does_not_duplicate_records(seeded, tmp_path):
    rows = [
        row(1, "Ayşe Yılmaz", "Peyzaj", "Patent", "Simaj", "Ankara Üni., Gazi Üni.", datetime(2026, 1, 1), None, "Tuz Lambası"),
        row(2, "Ayşe Yılmaz", "Peyzaj", "Patent", "Simaj", None, datetime(2026, 1, 1), None, "TUZ  LAMBASI"),  # dosyada mükerrer
        row(3, "Ayşe Yılmaz", "Peyzaj", "Patent", None, None, datetime(2026, 2, 1), None, "Tuz Lambası"),     # farklı tarih: mükerrer değil
    ]
    path = make_xlsx(tmp_path / "r.xlsx", HEADERS, rows)
    first = run(seeded, path)
    assert len(first.imported) == 2
    assert [r for r, why in first.skipped if why.startswith("mükerrer")] == [3]
    before = counts(seeded)
    second = run(seeded, path)
    assert second.imported == [] and len(second.skipped) == 3
    assert all(why.startswith("mükerrer") for _, why in second.skipped)
    assert second.created_applicants == second.created_departments == second.created_firms == []
    assert counts(seeded) == before == (2, 1, 1, 1, 2)


def test_skips_invalid_rows_dry_run_writes_nothing_and_errors_roll_back(seeded, tmp_path, monkeypatch):
    rows = [
        row(1, "Ali", "Bölüm X", "Patent", "Firma X", None, None, None, None),                    # başlık boş
        row(2, None, "Bölüm X", "Patent", "Firma X", None, None, None, "Başlıksız sahip"),         # başvuru sahibi boş
        row(3, "Veli", "Bölüm X", "Roket Bilimi", "Firma X", None, None, None, "Bilinmeyen tür"),  # tanınmayan tür
        row(4, "Veli", "Bölüm X", None, "Firma X", None, None, None, "Türsüz"),                    # tür boş
        row(5, "Ayşe", "Bölüm Y", "Marka", None, "Gazi Üni.", None, None, "Geçerli"),
    ]
    path = make_xlsx(tmp_path / "s.xlsx", HEADERS, rows)

    dry = run(seeded, path, apply=False)  # dry-run: hiçbir şey yazılmaz
    assert len(dry.imported) == 1 and counts(seeded) == (0, 0, 0, 0, 0)

    report = run(seeded, path)
    reasons = dict(report.skipped)
    assert reasons[2] == "başlık boş" and reasons[3] == "başvuru sahibi boş"
    assert "Roket Bilimi" in reasons[4] and reasons[5] == "FSMH türü boş"
    assert report.created_applicants == ["Ayşe"] and report.created_departments == ["Bölüm Y"] and report.created_firms == []
    assert [d.name for d in seeded.query(Department)] == ["Bölüm Y"]  # atlanan satırlar kayıt oluşturmaz
    assert counts(seeded) == (1, 1, 1, 0, 1)

    # tek transaction: ortada hata olursa hiçbir şey yazılmaz
    seeded.query(PatentPartner).delete()
    seeded.query(Patent).delete()
    seeded.commit()
    good = [row(i, f"Kişi {i}", None, "Patent", None, None, None, None, f"Buluş {i}") for i in range(1, 6)]
    path2 = make_xlsx(tmp_path / "t.xlsx", HEADERS, good)
    real = excel_import.parse_date
    calls = []

    def boom(value):
        calls.append(1)
        if len(calls) == 4:
            raise RuntimeError("yarıda hata")
        return real(value)

    monkeypatch.setattr(excel_import, "parse_date", boom)
    before = counts(seeded)
    with pytest.raises(RuntimeError):
        run(seeded, path2)
    assert counts(seeded) == before
