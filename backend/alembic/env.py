from logging.config import fileConfig

from alembic import context

import app.models  # noqa: F401  (Base.metadata tüm tabloları görsün)
from app.database import DB_PATH, Base, create_db_engine

config = context.config
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    raise RuntimeError("Offline mod desteklenmiyor; SQLite PRAGMA'ları için canlı bağlantı gerekir.")


def _run(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    # Testler hazır bir bağlantıyı config.attributes["connection"] ile verebilir.
    connection = config.attributes.get("connection")
    if connection is not None:
        _run(connection)
        return

    if config.config_file_name is not None:
        fileConfig(config.config_file_name, disable_existing_loggers=False)

    engine = create_db_engine(DB_PATH)  # PRAGMA'lar (foreign_keys=ON dahil) uygulanır
    try:
        with engine.connect() as connection:
            _run(connection)
    finally:
        engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
