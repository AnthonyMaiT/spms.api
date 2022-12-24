"""define-default-quarters

Revision ID: da6681a40080
Revises: 50829c2ded03
Create Date: 2022-12-23 17:40:00.666131

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'da6681a40080'
down_revision = '50829c2ded03'
branch_labels = None
depends_on = None

# define quarter_table in order to add to the db
quarter_table = sa.table('quarters', 
    sa.column('id', sa.Integer), sa.column('quarter', sa.String))

# adds quarters to db when upgrade
def upgrade() -> None:
    op.bulk_insert(quarter_table, 
        [
            {'quarter':'Quarter 1'},
            {'quarter':'Quarter 2'},
            {'quarter':'Quarter 3'},
            {"quarter":"Quarter 4"}
        ])
    pass

# removes quarters from db when downgrade
def downgrade() -> None:
    op.execute(
        quarter_table.delete().where(quarter_table.c.quarter == 'Quarter 1')
    )
    op.execute(
        quarter_table.delete().where(quarter_table.c.quarter == 'Quarter 2')
    )
    op.execute(
        quarter_table.delete().where(quarter_table.c.quarter == 'Quarter 3')
    )
    op.execute(
        quarter_table.delete().where(quarter_table.c.quarter == 'Quarter 4')
    )
    pass
