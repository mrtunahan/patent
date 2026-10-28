import json
from datetime import UTC, date, datetime

import pytest
from pydantic import TypeAdapter, ValidationError
from sqlalchemy.orm import Session

from app.database import Base, create_db_engine
from app.models import (
    Applicant,
    AttorneyFirm,
    Department,
    FsmhType,
    Patent,
    PatentPartner,
)
from app.schemas import (
    ApplicantIn,
    ApplicantRead,
    AttorneyFirmIn,
    AttorneyFirmRead,
    DepartmentIn,
    DepartmentRead,
    DuplicateWarning,
    ErrorResponse,
    FsmhTypeIn,
    FsmhTypeRead,
    Page,
    PatentIn,
    PatentListQuery,
    PatentListResponse,
    PatentRead,
    SettingsMap,
)


def fields_with_error(exc_info):
    return {e["loc"][0] if e["loc"] else "" for e in exc_info.value.errors()}


# --- kırpma, boş -> None / 422 ---

def test_required_text_trimmed_inner_spaces_untouched():
    a = ApplicantIn(full_name="  Ali   Veli  ")
    assert a.full_name == "Ali   Veli"


@pytest.mark.parametrize("blank", ["", "   ", "\t\n "])
def test_required_text_blank_is_422(blank):
    for model, field in [(ApplicantIn, "full_name"), (DepartmentIn, "name"),
                         (FsmhTypeIn, "name"), (AttorneyFirmIn, "name")]:
        with pytest.raises(ValidationError):
            model(**{field: blank})
    with pytest.raises(ValidationError):
        PatentIn(title=blank, applicant_id=1, fsmh_type_id=1)


def test_optional_text_blank_becomes_none_and_is_trimmed():
    assert ApplicantIn(full_name="A", email="   ").email is None
    assert ApplicantIn(full_name="A", email="  a@b.c ").email == "a@b.c"
    assert AttorneyFirmIn(name="F", contact_info="  \n ").contact_info is None
    assert AttorneyFirmIn(name="F", contact_info=" tel: 1  ").contact_info == "tel: 1"
    p = PatentIn(title="T", applicant_id=1, fsmh_type_id=1, notes="  not  ")
    assert p.notes == "not"
    assert PatentIn(title="T", applicant_id=1, fsmh_type_id=1, notes="  ").notes is None


def test_turkish_characters_preserved():
    p = PatentIn(title="  Modüler Işık İğne Şeker Çöp  ", applicant_id=1, fsmh_type_id=1)
    assert p.title == "Modüler Işık İğne Şeker Çöp"


# --- zorunlu alanlar ---

def test_required_fields_missing():
    with pytest.raises(ValidationError) as e:
        PatentIn()
    assert fields_with_error(e) == {"title", "applicant_id", "fsmh_type_id"}
    for model in (ApplicantIn, DepartmentIn, FsmhTypeIn, AttorneyFirmIn):
        with pytest.raises(ValidationError):
            model()


def test_defaults():
    a = ApplicantIn(full_name="A")
    assert (a.department_id, a.email, a.is_active) == (None, None, True)
    f = AttorneyFirmIn(name="F")
    assert (f.contact_info, f.is_active) == (None, True)
    assert FsmhTypeIn(name="T").sort_order == 0
    p = PatentIn(title="T", applicant_id=1, fsmh_type_id=1)
    assert p.partners == [] and p.department_id is None and p.attorney_firm_id is None
    assert p.application_date is None and p.notes is None
    assert PatentIn(title="T", applicant_id=1, fsmh_type_id=1).partners is not \
        PatentIn(title="T", applicant_id=1, fsmh_type_id=1).partners


# --- max_length ---

@pytest.mark.parametrize(
    "build, field, limit",
    [
        (lambda v: PatentIn(title=v, applicant_id=1, fsmh_type_id=1), "title", 500),
        (lambda v: ApplicantIn(full_name=v), "full_name", 200),
        (lambda v: ApplicantIn(full_name="A", email=v), "email", 200),
        (lambda v: DepartmentIn(name=v), "name", 200),
        (lambda v: AttorneyFirmIn(name=v), "name", 200),
        (lambda v: FsmhTypeIn(name=v), "name", 100),
        (lambda v: PatentIn(title="T", applicant_id=1, fsmh_type_id=1, partners=[v]), "partners", 200),
        (lambda v: SettingsMap and TypeAdapter(SettingsMap).validate_python({v: "x"}), "key", 100),
    ],
)
def test_max_length_boundaries(build, field, limit):
    build("a" * limit)  # tam sınır geçerli
    with pytest.raises(ValidationError):
        build("a" * (limit + 1))


def test_max_length_applies_after_trim():
    DepartmentIn(name=" " + "a" * 200 + " ")  # kırpma sonrası 200 -> geçerli
    with pytest.raises(ValidationError):
        DepartmentIn(name="a" * 201 + " ")


def test_text_columns_have_no_length_limit():
    long = "x" * 10_000
    assert len(AttorneyFirmIn(name="F", contact_info=long).contact_info) == 10_000
    assert len(PatentIn(title="T", applicant_id=1, fsmh_type_id=1, notes=long).notes) == 10_000


# --- extra="forbid" ---

@pytest.mark.parametrize("extra", ["id", "created_at", "updated_at", "deleted_at", "bogus"])
def test_input_extra_fields_forbidden(extra):
    with pytest.raises(ValidationError):
        ApplicantIn(full_name="A", **{extra: 1})
    with pytest.raises(ValidationError):
        DepartmentIn(name="D", **{extra: 1})
    with pytest.raises(ValidationError):
        FsmhTypeIn(name="T", **{extra: 1})
    with pytest.raises(ValidationError):
        AttorneyFirmIn(name="F", **{extra: 1})
    with pytest.raises(ValidationError):
        PatentIn(title="T", applicant_id=1, fsmh_type_id=1, **{extra: 1})
    with pytest.raises(ValidationError):
        PatentListQuery(**{extra: 1})


# --- partners ---

def test_partners_trimmed_blank_rejected_duplicates_not_checked_here():
    p = PatentIn(title="T", applicant_id=1, fsmh_type_id=1, partners=["  Ankara Üni. ", "Ankara Üni."])
    assert p.partners == ["Ankara Üni.", "Ankara Üni."]  # tekrar kontrolü servis katmanında
    with pytest.raises(ValidationError):
        PatentIn(title="T", applicant_id=1, fsmh_type_id=1, partners=["A", "  "])


def test_future_and_empty_application_date_accepted():
    p = PatentIn(title="T", applicant_id=1, fsmh_type_id=1, application_date="2099-12-31")
    assert p.application_date == date(2099, 12, 31)
    assert PatentIn(title="T", applicant_id=1, fsmh_type_id=1).application_date is None
    with pytest.raises(ValidationError):
        PatentIn(title="T", applicant_id=1, fsmh_type_id=1, application_date="31.12.2026")


# --- ORM -> Read (from_attributes) ---

@pytest.fixture
def session(tmp_path):
    engine = create_db_engine(tmp_path / "schemas.db")
    Base.metadata.create_all(engine)  # yalnızca test
    with Session(engine, expire_on_commit=False) as s:
        yield s
    engine.dispose()


def test_read_schemas_from_orm(session):
    dept = Department(name="Peyzaj Mimarlığı")
    firm = AttorneyFirm(name="Simaj", contact_info="x")
    applicant = Applicant(full_name="Ali Veli", email="a@b.c")
    ftype = FsmhType(name="Patent", sort_order=1)
    session.add_all([dept, firm, applicant, ftype])
    session.flush()
    patent = Patent(
        title="Tuz Lambası", applicant_id=applicant.id, fsmh_type_id=ftype.id,
        department_id=dept.id, attorney_firm_id=firm.id,
        application_date=date(2026, 3, 5), notes="Ödeme yapılacak",
        deleted_at=datetime(2026, 1, 1),
    )
    patent.partners = [PatentPartner(partner_name="Ankara Üni."), PatentPartner(partner_name="Çankırı Karatekin Üni.")]
    session.add(patent)
    session.commit()

    r = PatentRead.model_validate(patent)
    assert r.id == patent.id
    assert r.applicant.model_dump() == {"id": applicant.id, "full_name": "Ali Veli"}
    assert r.department.model_dump() == {"id": dept.id, "name": "Peyzaj Mimarlığı"}
    assert r.fsmh_type.model_dump() == {"id": ftype.id, "name": "Patent"}
    assert r.attorney_firm.model_dump() == {"id": firm.id, "name": "Simaj"}
    assert r.partners == ["Ankara Üni.", "Çankırı Karatekin Üni."]
    assert r.application_date == date(2026, 3, 5)
    assert "deleted_at" not in r.model_dump()
    assert "deleted_at" not in PatentRead.model_fields

    d = json.loads(r.model_dump_json())
    assert d["application_date"] == "2026-03-05"
    assert d["partners"] == ["Ankara Üni.", "Çankırı Karatekin Üni."]

    for model, obj in [(ApplicantRead, applicant), (DepartmentRead, dept),
                       (FsmhTypeRead, ftype), (AttorneyFirmRead, firm)]:
        read = model.model_validate(obj)
        assert read.id == obj.id
        assert read.created_at.tzinfo is UTC and read.updated_at.tzinfo is UTC
    assert ApplicantRead.model_validate(applicant).is_active is True
    assert FsmhTypeRead.model_validate(ftype).sort_order == 1
    assert AttorneyFirmRead.model_validate(firm).contact_info == "x"


def test_read_optional_relations_none(session):
    applicant = Applicant(full_name="A")
    ftype = FsmhType(name="Marka")
    session.add_all([applicant, ftype])
    session.flush()
    patent = Patent(title="T", applicant_id=applicant.id, fsmh_type_id=ftype.id)
    session.add(patent)
    session.commit()
    r = PatentRead.model_validate(patent)
    assert r.department is None and r.attorney_firm is None
    assert r.partners == [] and r.application_date is None and r.notes is None


def test_read_schemas_do_not_expose_unknown_fields():
    for model in (ApplicantRead, DepartmentRead, FsmhTypeRead, AttorneyFirmRead, PatentRead):
        assert "deleted_at" not in model.model_fields


# --- zaman damgası: naive -> UTC ---

def test_naive_datetime_treated_as_utc_and_json_iso():
    r = DepartmentRead.model_validate(
        {"id": 1, "name": "D", "created_at": datetime(2026, 3, 5, 10, 0, 0), "updated_at": datetime(2026, 3, 5, 10, 0, 0)}
    )
    assert r.created_at.tzinfo is UTC
    assert r.created_at == datetime(2026, 3, 5, 10, 0, 0, tzinfo=UTC)
    out = json.loads(r.model_dump_json())
    assert out["created_at"] in ("2026-03-05T10:00:00Z", "2026-03-05T10:00:00+00:00")


def test_aware_datetime_converted_to_utc():
    from datetime import timedelta, timezone

    plus3 = timezone(timedelta(hours=3))
    r = DepartmentRead.model_validate(
        {"id": 1, "name": "D", "created_at": datetime(2026, 3, 5, 13, 0, tzinfo=plus3),
         "updated_at": datetime(2026, 3, 5, 13, 0, tzinfo=plus3)}
    )
    assert r.created_at == datetime(2026, 3, 5, 10, 0, tzinfo=UTC)
    assert r.created_at.utcoffset().total_seconds() == 0


# --- PatentListQuery ---

def test_list_query_defaults():
    q = PatentListQuery()
    assert (q.page, q.page_size, q.sort_by, q.sort_dir) == (1, 25, "id", "asc")
    assert q.q is None and q.has_attorney is None
    assert q.applicant_id is q.department_id is q.fsmh_type_id is q.attorney_firm_id is None
    assert q.date_from is None and q.date_to is None


def test_list_query_limits():
    assert PatentListQuery(page=1, page_size=1).page_size == 1
    assert PatentListQuery(page=5, page_size=100).page_size == 100
    for bad in ({"page": 0}, {"page": -1}, {"page_size": 0}, {"page_size": 101}):
        with pytest.raises(ValidationError):
            PatentListQuery(**bad)


@pytest.mark.parametrize("field", ["id", "title", "applicant", "department", "fsmh_type",
                                   "attorney_firm", "application_date", "created_at"])
def test_list_query_valid_sort_by(field):
    assert PatentListQuery(sort_by=field).sort_by == field


def test_list_query_invalid_sort():
    for bad in ({"sort_by": "notes"}, {"sort_by": "deleted_at"}, {"sort_dir": "up"}, {"sort_dir": "ASC"}):
        with pytest.raises(ValidationError):
            PatentListQuery(**bad)
    assert PatentListQuery(sort_dir="desc").sort_dir == "desc"


def test_list_query_q_trim_and_blank():
    assert PatentListQuery(q="  tuz  lambası ").q == "tuz  lambası"
    assert PatentListQuery(q="   ").q is None
    assert PatentListQuery(q="").q is None


def test_list_query_date_range():
    PatentListQuery(date_from="2026-01-01", date_to="2026-01-01")
    PatentListQuery(date_from="2026-01-01")
    PatentListQuery(date_to="2026-01-01")
    with pytest.raises(ValidationError):
        PatentListQuery(date_from="2026-02-01", date_to="2026-01-01")


def test_list_query_has_attorney_bool():
    assert PatentListQuery(has_attorney=True).has_attorney is True
    assert PatentListQuery(has_attorney="false").has_attorney is False


# --- Page, Duplicate, Error ---

def test_page_serialization(session):
    applicant = Applicant(full_name="A")
    ftype = FsmhType(name="Patent")
    session.add_all([applicant, ftype])
    session.flush()
    patent = Patent(title="T", applicant_id=applicant.id, fsmh_type_id=ftype.id)
    session.add(patent)
    session.commit()
    resp = PatentListResponse(items=[PatentRead.model_validate(patent)], total=1, page=1, page_size=25)
    d = json.loads(resp.model_dump_json())
    assert set(d) == {"items", "total", "page", "page_size"}
    assert d["total"] == 1 and d["items"][0]["title"] == "T"
    assert PatentListResponse is not Page
    empty = Page[int](items=[], total=0, page=1, page_size=25)
    assert empty.model_dump() == {"items": [], "total": 0, "page": 1, "page_size": 25}


def test_duplicate_warning_and_error_response():
    w = DuplicateWarning(duplicate=True, detail="Mükerrer kayıt", existing_ids=[3, 7])
    assert w.model_dump() == {"duplicate": True, "detail": "Mükerrer kayıt", "existing_ids": [3, 7]}
    with pytest.raises(ValidationError):
        DuplicateWarning(duplicate=False, detail="x", existing_ids=[])
    with pytest.raises(ValidationError):
        DuplicateWarning(duplicate=True, detail="x")
    assert ErrorResponse(detail="Bulunamadı").model_dump() == {"detail": "Bulunamadı"}
    with pytest.raises(ValidationError):
        ErrorResponse()


# --- Settings ---

def test_settings_map():
    ta = TypeAdapter(SettingsMap)
    assert ta.validate_python({" institution_name ": " ÇAKÜ ", "default_page_size": "25", "empty": ""}) == {
        "institution_name": "ÇAKÜ", "default_page_size": "25", "empty": "",
    }
    assert ta.validate_python({}) == {}


@pytest.mark.parametrize(
    "bad",
    [{"": "x"}, {"   ": "x"}, {"k": 5}, {"k": None}, {"a": "1", " a ": "2"}, {"k" * 101: "x"}, ["k"]],
)
def test_settings_map_invalid(bad):
    with pytest.raises(ValidationError):
        TypeAdapter(SettingsMap).validate_python(bad)
