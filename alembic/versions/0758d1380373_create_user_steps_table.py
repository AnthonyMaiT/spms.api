"""create-user-steps-table

Revision ID: 0758d1380373
Revises: b7ba8dbe6795
Create Date: 2023-01-29 14:25:18.600161

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0758d1380373'
down_revision = 'b7ba8dbe6795'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user_steps',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('step', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('user_steps')
    # ### end Alembic commands ###
