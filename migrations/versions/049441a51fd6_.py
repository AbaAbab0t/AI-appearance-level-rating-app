"""empty message

Revision ID: 049441a51fd6
Revises: 67ea21639560
Create Date: 2021-12-19 23:23:13.832332

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '049441a51fd6'
down_revision = '67ea21639560'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('facefeature',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('face_feature', sa.Text(), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('facelandmark',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('face_landmark', sa.Text(), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('recomendation',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('friends_id', sa.Integer(), nullable=True),
    sa.Column('accept', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('recomendation')
    op.drop_table('facelandmark')
    op.drop_table('facefeature')
    # ### end Alembic commands ###
