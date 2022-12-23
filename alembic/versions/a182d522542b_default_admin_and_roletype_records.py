"""default_admin_and_roletype_records

Revision ID: a182d522542b
Revises: c7277cac56a8
Create Date: 2022-12-22 19:38:58.994527

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import table, column


# revision identifiers, used by Alembic.
revision = 'a182d522542b'
down_revision = 'c7277cac56a8'
branch_labels = None
depends_on = None

roletype_table = sa.table('roleTypes', 
    sa.column('id', sa.Integer), sa.column('role_type', sa.String))

user_table = table('users', sa.column('id', sa.Integer),
    column('username', sa.String), column('password', sa.String),
    column('role_type_id',sa.Integer), column('first_name', sa.String),
    column('last_name', sa.String))


def upgrade() -> None:
    op.bulk_insert(roletype_table, 
        [
            {'role_type':'Admin'},
            {'role_type':'Staff'},
            {'role_type':'Student'}
        ])
    op.bulk_insert(user_table, 
        [
            {'username':'admin', 'password':'$2b$12$0B9oxKYDFep.vFMIhbr37.b6uesi50W0Soy6ye5bNAAmCBQ9.Wjsi',
                'role_type_id':1, 'first_name':'Admin', 'last_name':''}
        ])
    pass


def downgrade() -> None:
    op.execute(
        roletype_table.delete().where(roletype_table.c.role_type == 'Admin')
    )
    op.execute(
        roletype_table.delete().where(roletype_table.c.role_type == 'Staff')
    )
    op.execute(
        roletype_table.delete().where(roletype_table.c.role_type == 'Student')
    )
    op.execute(
        user_table.delete().where(user_table.c.username == 'admin')
    )
    pass
