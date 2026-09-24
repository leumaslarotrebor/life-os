"""Memory model — persistent memory rows for LIFE OS (V1: PostgreSQL only, no vectors)."""

import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.connection import Base


class MemoryType(str, enum.Enum):
    short_term = "short_term"
    derived = "derived"


class Memory(Base):
    __tablename__ = "memories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    memory_type: Mapped[MemoryType] = mapped_column(
        Enum(MemoryType), nullable=False, default=MemoryType.short_term
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<Memory id={self.id} type={self.memory_type}>"
