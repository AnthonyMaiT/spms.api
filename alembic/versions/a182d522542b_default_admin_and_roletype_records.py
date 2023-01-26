"""default_admin_and_roletype_records

Revision ID: a182d522542b
Revises: c7277cac56a8
Create Date: 2022-12-22 19:38:58.994527

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import table, column
from app.utils import hash


# revision identifiers, used by Alembic.
revision = 'a182d522542b'
down_revision = 'c7277cac56a8'
branch_labels = None
depends_on = None

# define tables in order to add to the database
roletype_table = sa.table('roleTypes', 
    sa.column('id', sa.Integer), sa.column('role_type', sa.String))

user_table = table('users', sa.column('id', sa.Integer),
    column('username', sa.String), column('password', sa.String),
    column('role_type_id',sa.Integer), column('first_name', sa.String),
    column('last_name', sa.String))

# add password hash no matter the secret key
password = hash('123qwe')

def upgrade() -> None:
    # add default role_types to database
    op.bulk_insert(roletype_table, 
        [
            {'role_type':'Admin'},
            {'role_type':'Staff'},
            {'role_type':'Student'}
        ])
    # add default admin user to database
    op.bulk_insert(user_table, 
        [
            {'username':'admin', 'password':password,
                'role_type_id':1, 'first_name':'Admin', 'last_name':''}
        ])
    pass

# removes created role_types and admin from database when run
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
