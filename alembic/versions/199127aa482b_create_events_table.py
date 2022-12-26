"""create-events-table

Revision ID: 199127aa482b
Revises: da6681a40080
Create Date: 2022-12-24 09:49:03.983991

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '199127aa482b'
down_revision = 'da6681a40080'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('events',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('is_sport', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('events')
    # ### end Alembic commands ###