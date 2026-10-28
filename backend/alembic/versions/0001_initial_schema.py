"""initial schema

Revision ID: 0001
Revises: 
Create Date: 2026-10-28 22:01:31.441325

"""
from datetime import UTC, datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('attorney_firms',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('contact_info', sa.Text(), nullable=True),
    sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name'),
    sqlite_autoincrement=True
    )
    op.create_table('departments',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name'),
    sqlite_autoincrement=True
    )
    op.create_table('fsmh_types',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name'),
    sqlite_autoincrement=True
    )
    fsmh_types = sa.table(
        'fsmh_types',
        sa.column('name', sa.String),
        sa.column('sort_order', sa.Integer),
        sa.column('created_at', sa.DateTime),
        sa.column('updated_at', sa.DateTime),
    )
    now = datetime.now(UTC)
    op.bulk_insert(
        fsmh_types,
        [
            {'name': name, 'sort_order': order, 'created_at': now, 'updated_at': now}
            for order, name in enumerate(
                ['Patent', 'Faydalı Model', 'Tasarım Tescili', 'Marka'], start=1
            )
        ],
    )
    op.create_table('settings',
    sa.Column('key', sa.String(length=100), nullable=False),
    sa.Column('value', sa.Text(), nullable=False),
    sa.PrimaryKeyConstraint('key')
    )
    op.create_table('applicants',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('full_name', sa.String(length=200), nullable=False),
    sa.Column('department_id', sa.Integer(), nullable=True),
    sa.Column('email', sa.String(length=200), nullable=True),
    sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('full_name'),
    sqlite_autoincrement=True
    )
    op.create_table('patents',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('title', sa.String(length=500), nullable=False),
    sa.Column('applicant_id', sa.Integer(), nullable=False),
    sa.Column('department_id', sa.Integer(), nullable=True),
    sa.Column('fsmh_type_id', sa.Integer(), nullable=False),
    sa.Column('attorney_firm_id', sa.Integer(), nullable=True),
    sa.Column('application_date', sa.Date(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('deleted_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['applicant_id'], ['applicants.id'], ),
    sa.ForeignKeyConstraint(['attorney_firm_id'], ['attorney_firms.id'], ),
    sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ),
    sa.ForeignKeyConstraint(['fsmh_type_id'], ['fsmh_types.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sqlite_autoincrement=True
    )
    with op.batch_alter_table('patents', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_patents_applicant_id'), ['applicant_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_patents_application_date'), ['application_date'], unique=False)
        batch_op.create_index(batch_op.f('ix_patents_deleted_at'), ['deleted_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_patents_fsmh_type_id'), ['fsmh_type_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_patents_title'), ['title'], unique=False)

    op.create_table('patent_partners',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('patent_id', sa.Integer(), nullable=False),
    sa.Column('partner_name', sa.String(length=200), nullable=False),
    sa.ForeignKeyConstraint(['patent_id'], ['patents.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sqlite_autoincrement=True
    )


def downgrade() -> None:
    op.drop_table('patent_partners')
    with op.batch_alter_table('patents', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_patents_title'))
        batch_op.drop_index(batch_op.f('ix_patents_fsmh_type_id'))
        batch_op.drop_index(batch_op.f('ix_patents_deleted_at'))
        batch_op.drop_index(batch_op.f('ix_patents_application_date'))
        batch_op.drop_index(batch_op.f('ix_patents_applicant_id'))

    op.drop_table('patents')
    op.drop_table('applicants')
    op.drop_table('settings')
    op.drop_table('fsmh_types')
    op.drop_table('departments')
    op.drop_table('attorney_firms')
