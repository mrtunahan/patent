import os
import sqlite3
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app import database
from app.database import create_db_engine


@pytest.fixture
def engine(tmp_path):
    eng = create_db_engine(tmp_path / "sub" / "test.db")
    yield eng
    eng.dispose()


def pragma(conn, name):
    return conn.execute(text(f"PRAGMA {name}")).scalar()


def test_file_created_only_on_first_connect(engine):
    db_file = Path(engine.url.database)
    assert db_file.parent.is_dir()
    assert not db_file.exists()
    with engine.connect():
        pass
    assert db_file.exists()


def test_pragmas_applied(engine):
    with engine.connect() as conn:
        assert pragma(conn, "journal_mode") == "wal"
        assert pragma(conn, "foreign_keys") == 1
        assert pragma(conn, "synchronous") == 1  # NORMAL
        assert pragma(conn, "busy_timeout") == 5000


def test_pragmas_applied_on_every_new_connection(engine):
    with engine.connect() as first, engine.connect() as second:
        assert first.connection.dbapi_connection is not second.connection.dbapi_connection
        for conn in (first, second):
            assert pragma(conn, "journal_mode") == "wal"
            assert pragma(conn, "foreign_keys") == 1
            assert pragma(conn, "synchronous") == 1
            assert pragma(conn, "busy_timeout") == 5000


def test_foreign_keys_enforced(engine):
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE parent (id INTEGER PRIMARY KEY)"))
        conn.execute(
            text("CREATE TABLE child (id INTEGER PRIMARY KEY, parent_id INTEGER REFERENCES parent(id))")
        )
    with pytest.raises(IntegrityError):
        with engine.begin() as conn:
            conn.execute(text("INSERT INTO child (parent_id) VALUES (999)"))


def test_check_same_thread_disabled(engine):
    import threading

    errors = []
    with engine.connect() as conn:
        def use_in_other_thread():
            try:
                conn.execute(text("SELECT 1"))
            except Exception as exc:  # sqlite3.ProgrammingError beklenmez
                errors.append(exc)

        t = threading.Thread(target=use_in_other_thread)
        t.start()
        t.join()
    assert errors == []


def test_default_db_path_independent_of_cwd(tmp_path, monkeypatch):
    expected = Path(__file__).resolve().parents[2] / "data" / "patent.db"
    monkeypatch.chdir(tmp_path)
    assert database.DB_PATH == expected
    assert Path(database.engine.url.database) == expected
    assert Path(os.getcwd()) != expected.parent


def test_import_has_no_db_file_side_effect():
    import subprocess, sys

    backend = Path(__file__).resolve().parents[1]
    db_file = database.DB_PATH
    if db_file.exists():
        pytest.skip("data/patent.db zaten var")
    subprocess.run([sys.executable, "-c", "import app.database"], cwd=backend, check=True)
    assert not db_file.exists()


def test_get_db_yields_and_closes_session():
    gen = database.get_db()
    session = next(gen)
    assert session.is_active
    with pytest.raises(StopIteration):
        next(gen)
