"""durum, tescil tarihi, vekil firma alanları, Telif Hakkı türü

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-02 10:00:00

"""
from datetime import UTC, datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.core.text import normalize_tr

# revision identifiers, used by Alembic.
revision: str = '0002'
down_revision: Union[str, Sequence[str], None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NEW_TYPE = 'Telif Hakkı'


def upgrade() -> None:
    # ADD COLUMN (nullable): tablo yeniden oluşturulmaz, mevcut satırlar değişmez.
    op.add_column('patents', sa.Column('registration_date', sa.Date(), nullable=True))
    op.add_column('patents', sa.Column('status', sa.String(length=30), nullable=True))
    op.add_column('attorney_firms', sa.Column('tax_no', sa.String(length=20), nullable=True))
    op.add_column('attorney_firms', sa.Column('title', sa.String(length=300), nullable=True))
    op.add_column('attorney_firms', sa.Column('email', sa.String(length=200), nullable=True))

    # "Telif Hakkı" türü (idempotent: normalize edilmiş ad zaten varsa eklenmez)
    conn = op.get_bind()
    rows = conn.execute(sa.text('SELECT name, sort_order FROM fsmh_types')).all()
    if not any(normalize_tr(name) == normalize_tr(NEW_TYPE) for name, _ in rows):
        now = datetime.now(UTC)
        conn.execute(
            sa.text(
                'INSERT INTO fsmh_types (name, sort_order, created_at, updated_at) '
                'VALUES (:name, :sort_order, :now, :now)'
            ).bindparams(sa.bindparam('now', type_=sa.DateTime)),
            {'name': NEW_TYPE, 'sort_order': max((order for _, order in rows), default=0) + 1, 'now': now},
        )


def downgrade() -> None:
    # Hiçbir patente bağlı değilse "Telif Hakkı" silinir.
    op.execute(
        "DELETE FROM fsmh_types WHERE name = 'Telif Hakkı' "
        "AND id NOT IN (SELECT fsmh_type_id FROM patents)"
    )
    # SQLite >= 3.35 DROP COLUMN: batch tablo yeniden oluşturması yok, bu yüzden foreign_keys=ON
    # iken patent_partners CASCADE ile silinme riski de yok.
    for table, column in (
        ('attorney_firms', 'email'), ('attorney_firms', 'title'), ('attorney_firms', 'tax_no'),
        ('patents', 'status'), ('patents', 'registration_date'),
    ):
        op.execute(f'ALTER TABLE {table} DROP COLUMN {column}')
