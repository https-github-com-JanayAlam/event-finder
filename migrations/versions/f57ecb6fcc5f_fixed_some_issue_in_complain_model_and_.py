"""Fixed some issue in complain model and profile relationship

Revision ID: f57ecb6fcc5f
Revises: be2c9bf094e7
Create Date: 2021-11-24 22:37:53.169005

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f57ecb6fcc5f'
down_revision = 'be2c9bf094e7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('complain', sa.Column('complain_type', sa.Enum('GENERAL', 'HOST', 'ADMIN', name='role'), nullable=False))
    op.alter_column('complain', 'complained_by',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.drop_constraint('complain_complained_by_fkey', 'complain', type_='foreignkey')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_foreign_key('complain_complained_by_fkey', 'complain', 'profile', ['complained_by'], ['id'])
    op.alter_column('complain', 'complained_by',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.drop_column('complain', 'complain_type')
    # ### end Alembic commands ###
