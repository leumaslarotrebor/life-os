"""Monitor model — represents an active monitoring task in LIFE OS."""

import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.connection import Base


class MonitorStatus(str, enum.Enum):
    active = "active"
    paused = "paused"
    completed = "completed"
    cancelled = "cancelled"


class Monitor(Base):
    __tablename__ = "monitors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    condition: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Optional FK to the goal this monitor relates to
    related_goal: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("goals.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[MonitorStatus] = mapped_column(
        Enum(MonitorStatus), nullable=False, default=MonitorStatus.active
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<Monitor id={self.id} name={self.name!r} status={self.status}>"
