import datetime
import uuid

import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.dialects import postgresql

from backend.src.infrastructure import orm as orm_


class ProjectModel(orm_.Base):
    __tablename__ = "projects"

    id: orm.Mapped[uuid.UUID] = orm.mapped_column(
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    title: orm.Mapped[str] = orm.mapped_column(sa.String(200), nullable=False)
    short_description: orm.Mapped[str] = orm.mapped_column(sa.Text, nullable=False)
    full_description: orm.Mapped[str] = orm.mapped_column(sa.Text, default="")
    tags: orm.Mapped[str] = orm.mapped_column(sa.Text, default="")  # comma-separated
    github_url: orm.Mapped[str] = orm.mapped_column(sa.String(500), default="")
    live_url: orm.Mapped[str] = orm.mapped_column(sa.String(500), default="")
    cover_image: orm.Mapped[str] = orm.mapped_column(sa.String(500), default="")
    is_featured: orm.Mapped[bool] = orm.mapped_column(sa.Boolean, default=False, index=True)
    is_published: orm.Mapped[bool] = orm.mapped_column(sa.Boolean, default=False, index=True)
    sort_order: orm.Mapped[int] = orm.mapped_column(sa.Integer, default=0)
    created_at: orm.Mapped[datetime.datetime] = orm.mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        index=True,
    )
