"""Add-Point-For-Winners

Revision ID: b7ba8dbe6795
Revises: 59b5743011e4
Create Date: 2023-01-19 22:32:07.538728

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b7ba8dbe6795'
down_revision = '59b5743011e4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('student_winners', sa.Column('points', sa.Integer(), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('student_winners', 'points')
    # ### end Alembic commands ###
