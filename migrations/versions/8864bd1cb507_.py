"""empty message

Revision ID: 8864bd1cb507
Revises: e4666620d2e1
Create Date: 2025-06-20 14:18:46.325069

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '8864bd1cb507'
down_revision: Union[str, Sequence[str], None] = 'e4666620d2e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('blendshapes',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('training_id', sa.UUID(), nullable=False),
    sa.Column('timestamp', sa.Float(), nullable=False, comment='Seconds since training start'),
    sa.Column('scores', postgresql.JSONB(astext_type=sa.Text()), nullable=False, comment="Map of blendshape scores, e.g. {'jawOpen': 0.42}"),
    sa.ForeignKeyConstraint(['training_id'], ['trainings.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('blendshapes')
    # ### end Alembic commands ###
