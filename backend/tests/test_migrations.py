from pathlib import Path

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import inspect, text

from app import database
from app.database import Base, create_db_engine

ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"
TABLES = {
    "applicants", "departments", "fsmh_types", "attorney_firms",
    "patents", "patent_partners", "settings",
}


@pytest.fixture
def engine(tmp_path):
    eng = create_db_engine(tmp_path / "migrate.db")
    yield eng
    eng.dispose()


def make_cfg(connection):
    cfg = Config(str(ALEMBIC_INI))
    cfg.attributes["connection"] = connection
    return cfg


def upgrade(engine):
    with engine.begin() as conn:
        command.upgrade(make_cfg(conn), "head")


def downgrade(engine):
    with engine.begin() as conn:
        command.downgrade(make_cfg(conn), "base")


def tables(engine):
    return set(inspect(engine).get_table_names())


def test_upgrade_head_creates_tables(engine):
    upgrade(engine)
    assert tables(engine) == TABLES | {"alembic_version"}
    with engine.connect() as conn:
        assert conn.execute(text("SELECT version_num FROM alembic_version")).scalar() == "0002"
        assert conn.execute(text("PRAGMA journal_mode")).scalar() == "wal"
        assert conn.execute(text("PRAGMA foreign_keys")).scalar() == 1


def test_fsmh_seed(engine):
    upgrade(engine)
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT name, sort_order, created_at, updated_at FROM fsmh_types ORDER BY sort_order")
        ).all()
    assert [(r[0], r[1]) for r in rows] == [
        ("Patent", 1), ("Faydalı Model", 2), ("Tasarım Tescili", 3), ("Marka", 4), ("Telif Hakkı", 5),
    ]
    assert all(r[2] and r[3] for r in rows)


def test_settings_not_seeded(engine):
    upgrade(engine)
    with engine.connect() as conn:
        assert conn.execute(text("SELECT COUNT(*) FROM settings")).scalar() == 0


def test_models_and_migration_in_sync(engine):
    upgrade(engine)
    with engine.connect() as conn:
        ctx = MigrationContext.configure(
            conn, opts={"compare_type": True, "render_as_batch": True}
        )
        assert compare_metadata(ctx, Base.metadata) == []


def test_schema_details_after_migration(engine):
    upgrade(engine)
    insp = inspect(engine)
    assert insp.get_foreign_keys("patent_partners")[0]["options"].get("ondelete") == "CASCADE"
    for table in ("patents", "applicants"):
        assert all(not fk["options"].get("ondelete") for fk in insp.get_foreign_keys(table))
    indexed = {tuple(ix["column_names"]) for ix in insp.get_indexes("patents")}
    for col in ("title", "applicant_id", "fsmh_type_id", "application_date", "deleted_at"):
        assert (col,) in indexed
    with engine.connect() as conn:
        for table in TABLES - {"settings"}:
            ddl = conn.execute(
                text("SELECT sql FROM sqlite_master WHERE name = :t"), {"t": table}
            ).scalar()
            assert "AUTOINCREMENT" in ddl, table


def test_downgrade_then_upgrade_again(engine):
    upgrade(engine)
    downgrade(engine)
    assert tables(engine) <= {"alembic_version"}
    upgrade(engine)
    assert tables(engine) == TABLES | {"alembic_version"}
    with engine.connect() as conn:
        assert conn.execute(text("SELECT COUNT(*) FROM fsmh_types")).scalar() == 5


def test_upgrade_twice_is_noop(engine):
    upgrade(engine)
    upgrade(engine)
    with engine.connect() as conn:
        assert conn.execute(text("SELECT COUNT(*) FROM fsmh_types")).scalar() == 5
        assert conn.execute(text("SELECT COUNT(*) FROM alembic_version")).scalar() == 1
    assert tables(engine) == TABLES | {"alembic_version"}


def test_env_uses_db_path_regardless_of_cwd(tmp_path, monkeypatch):
    """Bağlantı verilmeden (gerçek kullanım yolu) env.py DB_PATH'i kullanır."""
    target = tmp_path / "data" / "via_env.db"
    monkeypatch.setattr(database, "DB_PATH", target)
    monkeypatch.chdir(tmp_path)
    command.upgrade(Config(str(ALEMBIC_INI)), "head")
    assert target.exists()
    eng = create_db_engine(target)
    try:
        assert tables(eng) == TABLES | {"alembic_version"}
    finally:
        eng.dispose()


def test_0002_is_idempotent_when_type_exists_with_different_spelling(engine):
    with engine.begin() as conn:
        command.upgrade(make_cfg(conn), "0001")
        conn.execute(text("INSERT INTO fsmh_types (name, sort_order, created_at, updated_at) VALUES ('TELİF  hakkı', 9, '2026-01-01', '2026-01-01')"))
    upgrade(engine)
    with engine.connect() as conn:
        assert conn.execute(text("SELECT COUNT(*) FROM fsmh_types")).scalar() == 5  # 4 seed + var olan; ikincisi eklenmedi


def test_0002_downgrade_drops_columns_keeps_data_and_linked_type(engine):
    upgrade(engine)
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO applicants (full_name, is_active, created_at, updated_at) VALUES ('A', 1, '2026-01-01', '2026-01-01')"))
        conn.execute(text("INSERT INTO patents (title, applicant_id, fsmh_type_id, status, created_at, updated_at) VALUES ('T', 1, 5, 'Reddedildi', '2026-01-01', '2026-01-01')"))
        conn.execute(text("INSERT INTO patent_partners (patent_id, partner_name) VALUES (1, 'Ortak')"))
        command.downgrade(make_cfg(conn), "0001")
    insp = inspect(engine)
    assert not {"status", "registration_date"} & {c["name"] for c in insp.get_columns("patents")}
    assert not {"tax_no", "title", "email"} & {c["name"] for c in insp.get_columns("attorney_firms")}
    with engine.connect() as conn:
        assert conn.execute(text("SELECT COUNT(*) FROM patents")).scalar() == 1
        assert conn.execute(text("SELECT COUNT(*) FROM patent_partners")).scalar() == 1  # CASCADE ile silinmedi
        assert conn.execute(text("SELECT COUNT(*) FROM fsmh_types WHERE name = 'Telif Hakkı'")).scalar() == 1  # bağlı tür kalır
