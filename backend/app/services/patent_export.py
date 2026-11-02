from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font
from openpyxl.utils import get_column_letter
from sqlalchemy.orm import Session

from app.schemas import PatentFilterQuery
from app.services.patents import filtered_patents

XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

# Madde 3 sütun sırası: (başlık, genişlik)
COLUMNS = [
    ("No", 7),
    ("Buluş Başlığı", 45),
    ("Başvuru Sahibi", 26),
    ("Bölüm / Birim", 26),
    ("FSMH Türü", 18),
    ("Vekil Firma", 24),
    ("Ortaklar & Oranları", 36),
    ("Başvuru Tarihi", 16),
    ("Tescil Tarihi", 16),
    ("Durum", 20),
    ("Notlar / Açıklama", 50),
]
_FORMULA_PREFIXES = ("=", "+", "-", "@")


def _set_text(cell, value: str | None) -> None:
    """Metin hücresi: tip açıkça string yapılır, böylece '=' ile başlayan değer formül olarak çalışmaz."""
    cell.value = value
    if value is None:
        return
    cell.data_type = "s"
    cell.alignment = Alignment(wrap_text=True, vertical="top")
    if value.startswith(_FORMULA_PREFIXES):
        cell.quotePrefix = True  # Excel'de hücre düzenlense de formüle dönüşmez


def build_workbook(db: Session, query: PatentFilterQuery) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Patent Takip"
    ws.append([title for title, _ in COLUMNS])
    for index, (title, width) in enumerate(COLUMNS, 1):
        ws.cell(row=1, column=index).font = Font(bold=True)
        ws.column_dimensions[get_column_letter(index)].width = width
    ws.freeze_panes = "A2"

    for number, patent in enumerate(filtered_patents(db, query), 1):
        row = number + 1
        ws.cell(row=row, column=1, value=number)  # 1'den sıra; sayfalama ofseti yok
        texts = [
            patent.title,
            patent.applicant.full_name,
            patent.department.name if patent.department else None,
            patent.fsmh_type.name,
            patent.attorney_firm.name if patent.attorney_firm else None,
            ", ".join(p.partner_name for p in patent.partners) or None,
        ]
        for offset, text in enumerate(texts, 2):
            _set_text(ws.cell(row=row, column=offset), text)
        for column, value in ((8, patent.application_date), (9, patent.registration_date)):
            date_cell = ws.cell(row=row, column=column, value=value)
            date_cell.number_format = "DD.MM.YYYY"
            date_cell.alignment = Alignment(horizontal="left", vertical="top")
        _set_text(ws.cell(row=row, column=10), patent.status)
        _set_text(ws.cell(row=row, column=11), patent.notes)

    buffer = BytesIO()
    wb.save(buffer)
    return buffer.getvalue()
