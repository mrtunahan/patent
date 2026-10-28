#!/usr/bin/env python
"""Excel aktarım scripti (Şartname Madde 12/13): data/source/patent-takip.xlsx -> data/patent.db.

Kullanım (backend sanal ortamının python'u ile):
    backend/.venv/bin/python scripts/excel_import.py                 # DRY-RUN: DB'ye yazmaz, rapor verir
    backend/.venv/bin/python scripts/excel_import.py --apply         # yazar (tek transaction)
    backend/.venv/bin/python scripts/excel_import.py --file yol.xlsx

DRY-RUN gerçek DB'ye hiç yazmaz: DB varsa kopyası, yoksa Alembic ile hazırlanan geçici DB üzerinde
aynı mantığı çalıştırır. --apply için `cd backend && alembic upgrade head` ile DB hazır olmalıdır.
Yalnızca Madde 3'teki 8 alan aktarılır; "No" ve şema dışı sütunlar (Madde 2.2) atlanır.
"""
from __future__ import annotations

import argparse
import re
import sqlite3
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND))

import openpyxl  # noqa: E402
from pydantic import ValidationError  # noqa: E402
from sqlalchemy import inspect, select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.core.text import normalize_tr  # noqa: E402
from app.models import Applicant, AttorneyFirm, Department, FsmhType, Patent, PatentPartner  # noqa: E402
from app.schemas import ApplicantIn, AttorneyFirmIn, DepartmentIn, PatentIn  # noqa: E402

DEFAULT_FILE = PROJECT_ROOT / "data" / "source" / "patent-takip.xlsx"

# Başlıklar ada göre (normalize_tr ile) eşlenir; sıraya güvenilmez.
HEADER_ALIASES = {
    "title": ["buluş başlığı"],
    "applicant": ["başvuru sahibi"],
    "department": ["bölüm", "bölüm / birim", "bölüm/birim"],
    "fsmh_type": ["fsmh türü"],
    "attorney_firm": ["vekil firma"],
    "partners": ["ortaklar ve oranları", "ortaklar & oranları", "ortaklar"],
    "application_date": ["başvuru tarihi"],
    "notes": ["notlar", "notlar / açıklama", "notlar/açıklama"],
}
REQUIRED_FIELDS = ("title", "applicant", "fsmh_type")
# "No" (yalnızca sıra numarası) ve Madde 2.2'deki şema dışı sütunlar bilerek atlanır.
IGNORED_HEADERS = {
    "no", "kapsam", "komisyon toplantı tarihi", "komisyon onay durumu", "komisyon oy/karar durumu",
    "komisyon oy / karar durumu", "mevcut durum", "masraf",
}
# Bölüm sütununda bölüm olmayan, başvuru sahibinin durumunu anlatan değerler: bölüm BOŞ bırakılır.
NOT_A_DEPARTMENT = {"ayrıldı"}

_RATIO = re.compile(r"%\s*\d+(?:[.,]\d+)?|\d+(?:[.,]\d+)?\s*%")
_EMPTY_BRACKETS = re.compile(r"\(\s*\)|\[\s*\]")
_PARTNER_SEPARATORS = re.compile(r"[,;/\n\r]+")
_DATE_DMY = re.compile(r"^(\d{1,2})[./-](\d{1,2})[./-](\d{4})$")
_DATE_ISO = re.compile(r"^(\d{4})-(\d{1,2})-(\d{1,2})$")


# --------------------------------------------------------------------------- ayrıştırma yardımcıları

def split_partners(raw: str) -> list[str]:
    """Ham ortak hücresini ad listesine böler: , ; / satır sonu ayraçtır, "%60" gibi oranlar atılır,
    normalize_tr ile tekrarlar elenir (ilk yazım korunur), boşlar atılır."""
    text = _EMPTY_BRACKETS.sub("", _RATIO.sub(" ", raw))
    names: list[str] = []
    seen: set[str] = set()
    for token in _PARTNER_SEPARATORS.split(text):
        name = token.strip().strip("-–:").strip()
        key = normalize_tr(name)
        if key and key not in seen:
            seen.add(key)
            names.append(name)
    return names


def parse_date(value) -> tuple[date | None, str]:
    """(tarih, durum): durum 'ok' | 'empty' | 'unparsed'. Excel tarihi veya GG.AA.YYYY / YYYY-AA-GG metni."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return None, "empty"
    if isinstance(value, datetime):
        return value.date(), "ok"
    if isinstance(value, date):
        return value, "ok"
    if isinstance(value, str):
        text = value.strip()
        try:
            if m := _DATE_DMY.match(text):
                return date(int(m[3]), int(m[2]), int(m[1])), "ok"
            if m := _DATE_ISO.match(text):
                return date(int(m[1]), int(m[2]), int(m[3])), "ok"
        except ValueError:  # örn. 31.02.2026
            pass
    return None, "unparsed"


def cell_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.date().isoformat()
    return str(value).strip()


def clean_department(raw: str) -> tuple[str, bool]:
    """(bölüm, bölüm_değil): tırnakları atıp bölüm olmayan işaretleri ("AYRILDI") boşa çevirir."""
    unquoted = raw.strip().strip("\"'“”‘’").strip()
    if normalize_tr(unquoted) in NOT_A_DEPARTMENT:
        return "", True
    return raw.strip(), False


def format_ranges(numbers: list[int]) -> str:
    parts, start, prev = [], None, None
    for n in sorted(numbers):
        if start is None:
            start = prev = n
        elif n == prev + 1:
            prev = n
        else:
            parts.append(str(start) if start == prev else f"{start}–{prev}")
            start = prev = n
    if start is not None:
        parts.append(str(start) if start == prev else f"{start}–{prev}")
    return ", ".join(parts)


# --------------------------------------------------------------------------- rapor

@dataclass
class Report:
    apply: bool = False
    sheet: str = ""
    read_rows: int = 0
    imported: list[dict] = field(default_factory=list)
    skipped: list[tuple[int, str]] = field(default_factory=list)  # (satır, neden)
    empty_rows: list[int] = field(default_factory=list)
    unresolved_dates: list[tuple[int, str]] = field(default_factory=list)
    ayrildi_rows: list[tuple[int, str]] = field(default_factory=list)
    undated_rows: int = 0
    partner_examples: list[tuple[str, list[str]]] = field(default_factory=list)
    created_departments: list[str] = field(default_factory=list)
    created_applicants: list[str] = field(default_factory=list)
    created_firms: list[str] = field(default_factory=list)
    ignored_headers: list[str] = field(default_factory=list)
    unknown_headers: list[str] = field(default_factory=list)


def format_report(report: Report, show: int = 5, source: str = "") -> str:
    lines = []
    add = lines.append
    add("=" * 72)
    add("EXCEL AKTARIMI — " + ("UYGULANDI (DB'ye yazıldı)" if report.apply else "DRY-RUN (DB'ye hiçbir şey yazılmadı)"))
    add("=" * 72)
    if source:
        add(f"Çalışma veritabanı : {source}")
    add(f"Sayfa              : {report.sheet}")
    add(f"Atlanan sütunlar   : {', '.join(report.ignored_headers) or '-'} (No ve şema dışı, Madde 2.2)")
    if report.unknown_headers:
        add(f"Tanınmayan sütunlar: {', '.join(report.unknown_headers)} (atlandı)")
    add("")
    skipped_nonempty = len(report.skipped)
    add(f"Okunan veri satırı : {report.read_rows}")
    add(f"{'Aktarılan' if report.apply else 'Aktarılacak':19}: {len(report.imported)}")
    add(f"Atlanan            : {skipped_nonempty + len(report.empty_rows)}")
    add("")
    add("--- Atlanan satırlar ---")
    if report.empty_rows:
        add(f"  satır {format_ranges(report.empty_rows)}: boş satır, atlandı ({len(report.empty_rows)} satır)")
    for row, reason in sorted(report.skipped):
        add(f"  satır {row}: {reason}")
    if not report.empty_rows and not report.skipped:
        add("  (yok)")
    add("")
    add("--- Oluşturulacak kayıtlar ---" if not report.apply else "--- Oluşturulan kayıtlar ---")
    for title, names in (("Bölüm", report.created_departments), ("Başvuru sahibi", report.created_applicants),
                         ("Vekil firma", report.created_firms)):
        add(f"  {title} ({len(names)}): {'; '.join(names) or '-'}")
    add("")
    add("--- 'AYRILDI' satırları (bölüm BOŞ bırakıldı) ---")
    if report.ayrildi_rows:
        for row, applicant in report.ayrildi_rows:
            add(f"  satır {row}: {applicant}")
    else:
        add("  (yok)")
    add("")
    add("--- Tarih ---")
    add(f"  tarihi boş, tarihsiz aktarılan: {report.undated_rows}")
    if report.unresolved_dates:
        add("  tarihi ÇÖZÜLEMEYEN (tarihsiz aktarıldı):")
        for row, raw in report.unresolved_dates:
            add(f"    satır {row}: {raw!r}")
    else:
        add("  çözülemeyen tarih: yok")
    add("")
    add("--- Ortaklar (ham hücre -> bölünmüş liste; ayrık değerler) ---")
    for raw, names in report.partner_examples:
        add(f"  {raw!r} -> {names}")
    if not report.partner_examples:
        add("  (ortak yok)")
    add("")
    add(f"--- İlk {min(show, len(report.imported))} kayıt (tam hâl) ---")
    for rec in report.imported[:show]:
        add(f"  [satır {rec['row']}]")
        for key in ("title", "applicant", "department", "fsmh_type", "attorney_firm", "application_date", "partners", "notes"):
            add(f"    {key:16}: {rec[key]!r}")
    return "\n".join(lines)


# --------------------------------------------------------------------------- aktarım

def read_sheet(path: Path):
    wb = openpyxl.load_workbook(path, data_only=True)
    return wb.worksheets[0]


def map_headers(ws, report: Report) -> dict[str, int]:
    """alan -> sütun numarası (ada göre). Zorunlu başlık yoksa ValueError."""
    columns: dict[str, int] = {}
    for idx, cell in enumerate(ws[1], start=1):
        if cell.value is None:
            continue
        key = normalize_tr(str(cell.value))
        field_name = next((f for f, aliases in HEADER_ALIASES.items() if key in aliases), None)
        if field_name:
            columns.setdefault(field_name, idx)
        elif key in IGNORED_HEADERS:
            report.ignored_headers.append(str(cell.value).strip())
        else:
            report.unknown_headers.append(str(cell.value).strip())
    missing = [f for f in REQUIRED_FIELDS if f not in columns]
    if missing:
        raise ValueError(f"Zorunlu sütun başlığı bulunamadı: {', '.join(missing)}")
    return columns


def import_rows(ws, db: Session, apply: bool, report: Report | None = None) -> Report:
    """Satırları işler. Tek transaction: apply ise sonda commit, değilse rollback; hata olursa rollback."""
    report = report or Report()
    report.apply = apply
    report.sheet = ws.title
    try:
        columns = map_headers(ws, report)
        fsmh_types = {normalize_tr(t.name): t for t in db.scalars(select(FsmhType))}
        applicants = {normalize_tr(a.full_name): a for a in db.scalars(select(Applicant))}
        departments = {normalize_tr(d.name): d for d in db.scalars(select(Department))}
        firms = {normalize_tr(f.name): f for f in db.scalars(select(AttorneyFirm))}
        seen: dict[tuple, str] = {  # mükerrer anahtarı: normalize başlık + başvuru sahibi + tarih
            (normalize_tr(p.title), p.applicant_id, p.application_date): f"veritabanında #{p.id}"
            for p in db.scalars(select(Patent).where(Patent.deleted_at.is_(None)))
        }
        partner_seen: set[str] = set()

        def get(row: int, name: str):
            col = columns.get(name)
            return ws.cell(row, col).value if col else None

        for row in range(2, ws.max_row + 1):
            raw = {name: get(row, name) for name in HEADER_ALIASES}
            if all(cell_text(v) == "" for v in raw.values()):
                report.empty_rows.append(row)
                continue
            report.read_rows += 1

            title, applicant_name = cell_text(raw["title"]), cell_text(raw["applicant"])
            if not title:
                report.skipped.append((row, "başlık boş"))
                continue
            if not applicant_name:
                report.skipped.append((row, "başvuru sahibi boş"))
                continue
            fsmh_raw = cell_text(raw["fsmh_type"])
            if not fsmh_raw:
                report.skipped.append((row, "FSMH türü boş"))
                continue
            fsmh_type = fsmh_types.get(normalize_tr(fsmh_raw))
            if fsmh_type is None:
                report.skipped.append((row, f"tanınmayan FSMH türü: {fsmh_raw!r}"))
                continue

            department_name, not_department = clean_department(cell_text(raw["department"]))
            if not_department:
                report.ayrildi_rows.append((row, applicant_name))
            firm_name = cell_text(raw["attorney_firm"])
            partners_raw = cell_text(raw["partners"])
            partners = split_partners(partners_raw)
            application_date, date_status = parse_date(raw["application_date"])

            try:  # API ile aynı kırpma/uzunluk kuralları
                patent_in = PatentIn(
                    title=title, applicant_id=1, fsmh_type_id=1, application_date=application_date,
                    notes=cell_text(raw["notes"]) or None, partners=partners,
                )
                applicant_in = ApplicantIn(full_name=applicant_name)
                department_in = DepartmentIn(name=department_name) if department_name else None
                firm_in = AttorneyFirmIn(name=firm_name) if firm_name else None
            except ValidationError as exc:
                first = exc.errors()[0]
                report.skipped.append((row, f"geçersiz alan {'.'.join(map(str, first['loc']))}: {first['msg']}"))
                continue

            applicant = applicants.get(normalize_tr(applicant_in.full_name))
            if applicant is not None:  # yeni başvuru sahibi mükerrer olamaz
                key = (normalize_tr(patent_in.title), applicant.id, patent_in.application_date)
                if key in seen:
                    report.skipped.append((row, f"mükerrer (başlık+başvuru sahibi+tarih), {seen[key]}"))
                    continue

            # Satır kabul edildi: eksik lookup kayıtlarını oluştur (varsayılan bölüm NULL kalır).
            if applicant is None:
                applicant = Applicant(full_name=applicant_in.full_name, department_id=None)
                db.add(applicant)
                applicants[normalize_tr(applicant.full_name)] = applicant
                report.created_applicants.append(applicant.full_name)
            department = None
            if department_in:
                department = departments.get(normalize_tr(department_in.name))
                if department is None:
                    department = Department(name=department_in.name)
                    db.add(department)
                    departments[normalize_tr(department.name)] = department
                    report.created_departments.append(department.name)
            firm = None
            if firm_in:
                firm = firms.get(normalize_tr(firm_in.name))
                if firm is None:
                    firm = AttorneyFirm(name=firm_in.name)
                    db.add(firm)
                    firms[normalize_tr(firm.name)] = firm
                    report.created_firms.append(firm.name)
            db.flush()  # yeni kayıtların id'leri

            patent = Patent(
                title=patent_in.title, applicant_id=applicant.id,
                department_id=department.id if department else None, fsmh_type_id=fsmh_type.id,
                attorney_firm_id=firm.id if firm else None, application_date=patent_in.application_date,
                notes=patent_in.notes, partners=[PatentPartner(partner_name=n) for n in patent_in.partners],
            )
            db.add(patent)
            db.flush()
            seen[(normalize_tr(patent.title), applicant.id, patent.application_date)] = f"dosyada satır {row}"

            if date_status == "empty":
                report.undated_rows += 1
            elif date_status == "unparsed":
                report.unresolved_dates.append((row, cell_text(raw["application_date"])))
            if partners_raw and normalize_tr(partners_raw) not in partner_seen:
                partner_seen.add(normalize_tr(partners_raw))
                report.partner_examples.append((partners_raw, partners))
            report.imported.append({
                "row": row, "title": patent.title, "applicant": applicant.full_name,
                "department": department.name if department else None, "fsmh_type": fsmh_type.name,
                "attorney_firm": firm.name if firm else None,
                "application_date": patent.application_date.isoformat() if patent.application_date else None,
                "partners": list(patent_in.partners), "notes": patent.notes,
            })

        if apply:
            db.commit()
        else:
            db.rollback()
    except BaseException:
        db.rollback()  # hata olursa hiçbir şey yazılmaz
        raise
    return report


# --------------------------------------------------------------------------- DB seçimi ve CLI

def _migrated_temp_engine(tmp: Path):
    from alembic import command
    from alembic.config import Config

    from app.database import create_db_engine

    engine = create_db_engine(tmp / "dry-run.db")
    cfg = Config(str(BACKEND / "alembic.ini"))
    with engine.begin() as conn:
        cfg.attributes["connection"] = conn
        command.upgrade(cfg, "head")
    return engine


def run_dry_run(path: Path, show: int) -> tuple[Report, str]:
    """Gerçek DB'ye dokunmadan: DB varsa kopyası, yoksa Alembic ile hazırlanmış geçici DB."""
    from app.database import DB_PATH, create_db_engine

    with tempfile.TemporaryDirectory() as tmp_name:
        tmp = Path(tmp_name)
        if DB_PATH.exists():
            copy = tmp / "copy.db"
            src = sqlite3.connect(DB_PATH)
            dst = sqlite3.connect(copy)
            src.backup(dst)
            src.close()
            dst.close()
            engine = create_db_engine(copy)
            source = f"{DB_PATH} (kopyası üzerinde; gerçek DB'ye yazılmadı)"
        else:
            engine = _migrated_temp_engine(tmp)
            source = f"{DB_PATH} yok -> boş şemalı geçici DB (Alembic head; gerçek DB oluşturulmadı)"
        try:
            with Session(engine, expire_on_commit=False) as db:
                report = import_rows(read_sheet(path), db, apply=False)
        finally:
            engine.dispose()
    return report, source


def run_apply(path: Path) -> tuple[Report, str]:
    from app.database import DB_PATH, SessionLocal, engine

    if not DB_PATH.exists():
        raise SystemExit(f"HATA: {DB_PATH} yok. Önce şemayı hazırlayın: cd backend && alembic upgrade head")
    if "patents" not in inspect(engine).get_table_names():
        raise SystemExit("HATA: veritabanında şema yok. Önce: cd backend && alembic upgrade head")
    with SessionLocal() as db:
        report = import_rows(read_sheet(path), db, apply=True)
    return report, str(DB_PATH)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Patent takip Excel aktarımı (varsayılan: DRY-RUN)")
    parser.add_argument("--file", type=Path, default=DEFAULT_FILE, help=f"xlsx yolu (varsayılan: {DEFAULT_FILE})")
    parser.add_argument("--apply", action="store_true", help="DB'ye yazar (tek transaction); verilmezse dry-run")
    parser.add_argument("--show", type=int, default=5, help="raporda tam hâliyle gösterilecek kayıt sayısı")
    args = parser.parse_args(argv)

    if not args.file.exists():
        print(f"HATA: dosya bulunamadı: {args.file}", file=sys.stderr)
        return 2
    try:
        report, source = run_apply(args.file) if args.apply else run_dry_run(args.file, args.show)
    except ValueError as exc:
        print(f"HATA: {exc}", file=sys.stderr)
        return 2
    print(format_report(report, args.show, source))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
