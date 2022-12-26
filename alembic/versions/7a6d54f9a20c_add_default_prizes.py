"""add-default-prizes

Revision ID: 7a6d54f9a20c
Revises: d92b9c92528d
Create Date: 2022-12-26 10:27:40.920263

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7a6d54f9a20c'
down_revision = 'd92b9c92528d'
branch_labels = None
depends_on = None

# define prizes table to add to db
prizes_table = sa.table('prizes', sa.column('name', sa.String), sa.column('level', sa.Integer))

# adds default rewards to the prizes table in db
def upgrade() -> None:
    op.bulk_insert(prizes_table,
    [
        {"name":"Great Student Reward", "level":1},
        {"name":"5$ Mcdonald's gift card", "level":2},
        {"name":"School Tshirt", "level":3}
    ])
    pass

# would remove the above fields from db when downgraded
def downgrade() -> None:
    op.execute(
        prizes_table.delete().where(prizes_table.c.name == "Great Student Reward")
    )
    op.execute(
        prizes_table.delete().where(prizes_table.c.name == "5$ Mcdonald's gift card")
    )
    op.execute(
        prizes_table.delete().where(prizes_table.c.name == "School Tshirt")
    )
    pass
