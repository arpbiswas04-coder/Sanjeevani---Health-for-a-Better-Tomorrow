"""Transactional cursor allocation: the singleton row lock is held until commit."""
from uuid import UUID
from sqlalchemy import BigInteger, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models.platform import Record

CLOCK_ID = UUID('00000000-0000-0000-0000-000000000001')


class SyncClock(Record, Base):
    __tablename__ = 'sync_clock'
    sequence: Mapped[int] = mapped_column(BigInteger, default=0)


class SyncChange(Record, Base):
    __tablename__ = 'sync_changes'
    sequence: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    kind: Mapped[str] = mapped_column(String(30))
    facility_id: Mapped[UUID] = mapped_column(ForeignKey('facilities.id'), index=True)
    entity_id: Mapped[UUID]
    payload: Mapped[dict] = mapped_column(JSON)
