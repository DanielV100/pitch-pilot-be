"""merge heads

Revision ID: f01ea0cfd94f
Revises: 81b9eb892078, cff98534dec4
Create Date: 2025-06-23 20:57:26.917686

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f01ea0cfd94f'
down_revision: Union[str, Sequence[str], None] = ('81b9eb892078', 'cff98534dec4')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
