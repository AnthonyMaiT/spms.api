"""add-default-events

Revision ID: b243f639a2ec
Revises: 199127aa482b
Create Date: 2022-12-24 09:53:03.420390

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b243f639a2ec'
down_revision = '199127aa482b'
branch_labels = None
depends_on = None


# define events in order to add to the db
events_table = sa.table('events', 
    sa.column('id', sa.Integer), sa.column('name', sa.String), sa.column('is_sport', sa.Boolean))

# adds default events to db when upgrade
def upgrade() -> None:
    op.bulk_insert(events_table, 
        [
            {'name':"Men's Basketball", 'is_sport': True},
            {'name':'Football', 'is_sport': True},
            {'name':"Women's Tennis", 'is_sport': True},
            {'name':'Wrestling', 'is_sport': True},
            {'name':'Swim and Dive', 'is_sport': True},
            {'name':'Movie Night', 'is_sport': False},
            {'name':'School Play', 'is_sport': False},
            {'name':'International Night', 'is_sport': False},
            {'name':'Field Day', 'is_sport': False},
            {'name':'Book Fair', 'is_sport': False}
        ])
    pass

# removes default events from db when downgrade
def downgrade() -> None:
    op.execute(
        events_table.delete().where(events_table.c.name == "Men's Basketball")
    )
    op.execute(
        events_table.delete().where(events_table.c.name == 'Football')
    )
    op.execute(
        events_table.delete().where(events_table.c.name == "Women's Tennis")
    )
    op.execute(
        events_table.delete().where(events_table.c.name == 'Wrestling')
    )
    op.execute(
        events_table.delete().where(events_table.c.name == 'Swim and Dive')
    )
    op.execute(
        events_table.delete().where(events_table.c.name == 'Movie Night')
    )
    op.execute(
        events_table.delete().where(events_table.c.name == 'School Play')
    )
    op.execute(
        events_table.delete().where(events_table.c.name == 'International Night')
    )
    op.execute(
        events_table.delete().where(events_table.c.name == 'Field Day')
    )
    op.execute(
        events_table.delete().where(events_table.c.name == 'Book Fair')
    )
    pass
