import time
from datetime import date

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import Base, create_db_engine
from app.models import (
    Applicant,
    AttorneyFirm,
    Department,
    FsmhType,
    Patent,
    PatentPartner,
    Setting,
)


@pytest.fixture
def engine(tmp_path):
    eng = create_db_engine(tmp_path / "test.db")
    Base.metadata.create_all(eng)  # yalnızca test; üretimde Alembic
    yield eng
    eng.dispose()


@pytest.fixture
def session(engine):
    with Session(engine, expire_on_commit=False) as s:
        yield s


def make_patent(session, title="Buluş", **kw):
    applicant = session.query(Applicant).first() or Applicant(full_name="Ali Veli")
    fsmh = session.query(FsmhType).first() or FsmhType(name="Patent")
    session.add_all([applicant, fsmh])
    session.flush()
    patent = Patent(title=title, applicant_id=applicant.id, fsmh_type_id=fsmh.id, **kw)
    session.add(patent)
    session.commit()
    return patent


def cols(engine, table):
    return {c["name"]: c for c in inspect(engine).get_columns(table)}


# --- şema ---

def test_all_tables_present(engine):
    assert set(inspect(engine).get_table_names()) == {
        "applicants", "departments", "fsmh_types", "attorney_firms",
        "patents", "patent_partners", "settings",
    }


EXPECTED = {
    "applicants": {
        "id": False, "full_name": False, "department_id": True, "email": True,
        "is_active": False, "created_at": False, "updated_at": False,
    },
    "departments": {"id": False, "name": False, "created_at": False, "updated_at": False},
    "fsmh_types": {
        "id": False, "name": False, "sort_order": False, "created_at": False, "updated_at": False,
    },
    "attorney_firms": {
        "id": False, "name": False, "contact_info": True, "is_active": False,
        "created_at": False, "updated_at": False,
    },
    "patents": {
        "id": False, "title": False, "applicant_id": False, "department_id": True,
        "fsmh_type_id": False, "attorney_firm_id": True, "application_date": True,
        "notes": True, "deleted_at": True, "created_at": False, "updated_at": False,
    },
    "patent_partners": {"id": False, "patent_id": False, "partner_name": False},
    "settings": {"key": False, "value": False},
}


@pytest.mark.parametrize("table", EXPECTED)
def test_columns_and_nullability(engine, table):
    actual = cols(engine, table)
    assert set(actual) == set(EXPECTED[table])
    # is_active / sort_order / created_at / updated_at: şartname NULL durumunu belirtmez; NOT NULL seçildi
    for name, nullable in EXPECTED[table].items():
        if name in ("id", "key"):
            continue
        assert actual[name]["nullable"] is nullable, f"{table}.{name}"


def test_string_lengths(engine):
    expected = {
        ("applicants", "full_name"): 200, ("applicants", "email"): 200,
        ("departments", "name"): 200, ("fsmh_types", "name"): 100,
        ("attorney_firms", "name"): 200, ("patents", "title"): 500,
        ("patent_partners", "partner_name"): 200, ("settings", "key"): 100,
    }
    for (table, col), length in expected.items():
        assert cols(engine, table)[col]["type"].length == length, f"{table}.{col}"


def test_autoincrement_in_ddl(engine):
    with engine.connect() as conn:
        for table in EXPECTED:
            ddl = conn.execute(
                text("SELECT sql FROM sqlite_master WHERE name = :t"), {"t": table}
            ).scalar()
            if table == "settings":
                assert "AUTOINCREMENT" not in ddl
            else:
                assert "AUTOINCREMENT" in ddl, table


def test_no_timestamps_on_partners_and_settings_and_no_id_on_settings(engine):
    for table in ("patent_partners", "settings"):
        names = set(cols(engine, table))
        assert not names & {"created_at", "updated_at"}
    assert "id" not in cols(engine, "settings")
    assert [c for c in inspect(engine).get_pk_constraint("settings")["constrained_columns"]] == ["key"]


def test_patent_indexes(engine):
    indexed = {
        tuple(ix["column_names"]) for ix in inspect(engine).get_indexes("patents")
    }
    for col in ("title", "applicant_id", "fsmh_type_id", "application_date", "deleted_at"):
        assert (col,) in indexed, col


def test_partner_fk_cascade_and_other_fks_have_no_ondelete(engine):
    insp = inspect(engine)
    partner_fk = insp.get_foreign_keys("patent_partners")[0]
    assert partner_fk["options"].get("ondelete") == "CASCADE"
    for table in ("patents", "applicants"):
        for fk in insp.get_foreign_keys(table):
            assert not fk["options"].get("ondelete"), (table, fk)


# --- kısıtlar ---

@pytest.mark.parametrize(
    "factory",
    [
        lambda: (Applicant(full_name="A"), Applicant(full_name="A")),
        lambda: (Department(name="D"), Department(name="D")),
        lambda: (FsmhType(name="F"), FsmhType(name="F")),
        lambda: (AttorneyFirm(name="V"), AttorneyFirm(name="V")),
    ],
)
def test_unique_violation(session, factory):
    first, second = factory()
    session.add(first)
    session.commit()
    session.add(second)
    with pytest.raises(IntegrityError):
        session.commit()


def test_not_null_violations(session):
    for obj in (Applicant(), Department(), FsmhType(), AttorneyFirm(), Setting(key="k")):
        session.add(obj)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

    ap = Applicant(full_name="X")
    ft = FsmhType(name="T")
    session.add_all([ap, ft])
    session.commit()
    bad = [
        Patent(applicant_id=ap.id, fsmh_type_id=ft.id),              # title yok
        Patent(title="t", fsmh_type_id=ft.id),                       # applicant_id yok
        Patent(title="t", applicant_id=ap.id),                       # fsmh_type_id yok
    ]
    for p in bad:
        session.add(p)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

    patent = make_patent(session)
    session.add(PatentPartner(patent_id=patent.id))                  # partner_name yok
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()
    session.add(PatentPartner(partner_name="Ankara Üni."))           # patent_id yok
    with pytest.raises(IntegrityError):
        session.commit()


def test_foreign_keys_enforced(session):
    ft = FsmhType(name="T")
    session.add(ft)
    session.commit()
    session.add(Patent(title="t", applicant_id=999, fsmh_type_id=ft.id))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()
    session.add(Applicant(full_name="Y", department_id=999))
    with pytest.raises(IntegrityError):
        session.commit()


def test_cannot_delete_applicant_with_patent(session):
    patent = make_patent(session)
    applicant = session.get(Applicant, patent.applicant_id)
    session.delete(applicant)
    with pytest.raises(IntegrityError):
        session.commit()


def test_cannot_delete_referenced_lookups(engine, session):
    dept = Department(name="Bölüm")
    firm = AttorneyFirm(name="Simaj")
    session.add_all([dept, firm])
    session.flush()
    make_patent(session, department_id=dept.id, attorney_firm_id=firm.id)
    for table in ("departments", "attorney_firms", "fsmh_types"):
        with pytest.raises(IntegrityError):
            with engine.begin() as conn:
                conn.execute(text(f"DELETE FROM {table}"))


def test_partner_cascade_on_physical_delete(session, engine):
    patent = make_patent(session)
    patent.partners.append(PatentPartner(partner_name="Ankara Üni."))
    patent.partners.append(PatentPartner(partner_name="Çankırı Karatekin Üni."))
    session.commit()
    assert session.query(PatentPartner).count() == 2
    session.delete(patent)
    session.commit()
    assert session.query(PatentPartner).count() == 0

    # ORM dışı (ham SQL) silmede de DB seviyesinde CASCADE çalışır
    patent2 = make_patent(session, title="İkinci")
    patent2.partners.append(PatentPartner(partner_name="X"))
    session.commit()
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM patents WHERE id = :i"), {"i": patent2.id})
    assert session.query(PatentPartner).count() == 0


# --- varsayılanlar ve zaman damgaları ---

def test_defaults(session):
    ap = Applicant(full_name="A")
    firm = AttorneyFirm(name="F")
    ft = FsmhType(name="T")
    session.add_all([ap, firm, ft])
    session.commit()
    assert ap.is_active is True
    assert firm.is_active is True
    assert ft.sort_order == 0


def test_server_defaults_apply_on_raw_insert(engine):
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO applicants (full_name, created_at, updated_at) VALUES ('R', '2026-01-01', '2026-01-01')")
        )
        conn.execute(
            text("INSERT INTO fsmh_types (name, created_at, updated_at) VALUES ('R', '2026-01-01', '2026-01-01')")
        )
        assert conn.execute(text("SELECT is_active FROM applicants")).scalar() == 1
        assert conn.execute(text("SELECT sort_order FROM fsmh_types")).scalar() == 0


def test_deleted_at_defaults_null_and_other_optionals(session):
    patent = make_patent(session)
    assert patent.deleted_at is None
    assert patent.application_date is None
    assert patent.notes is None
    assert patent.department_id is None
    assert patent.attorney_firm_id is None


def test_timestamps_filled_and_updated_at_advances(session):
    objs = [
        Applicant(full_name="A"), Department(name="D"), FsmhType(name="T"),
        AttorneyFirm(name="F"),
    ]
    session.add_all(objs)
    session.commit()
    patent = make_patent(session, application_date=date(2026, 3, 5))
    for o in (*objs, patent):
        assert o.created_at is not None and o.updated_at is not None
        assert o.created_at.tzinfo is not None  # UTC, tz-aware

    for o, field, value in [
        (objs[0], "full_name", "B"), (objs[1], "name", "E"),
        (objs[2], "name", "U"), (objs[3], "name", "G"), (patent, "title", "Yeni"),
    ]:
        before = o.updated_at
        created = o.created_at
        time.sleep(0.01)
        setattr(o, field, value)
        session.commit()
        session.refresh(o)
        assert o.updated_at > before.replace(tzinfo=o.updated_at.tzinfo), type(o)
        assert o.created_at.replace(tzinfo=None) == created.replace(tzinfo=None)


def test_date_stored_as_iso(session, engine):
    make_patent(session, application_date=date(2026, 3, 5))
    with engine.connect() as conn:
        assert conn.execute(text("SELECT application_date FROM patents")).scalar() == "2026-03-05"


def test_setting_roundtrip(session):
    session.add(Setting(key="institution_name", value="ÇAKÜ"))
    session.commit()
    assert session.get(Setting, "institution_name").value == "ÇAKÜ"
