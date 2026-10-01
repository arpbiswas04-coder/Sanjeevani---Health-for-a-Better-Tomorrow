from datetime import datetime
from uuid import UUID
from sqlalchemy import ForeignKey, String, UniqueConstraint, JSON, CheckConstraint, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models.platform import Record


class MutationReceipt(Record, Base):
    __tablename__ = 'mutation_receipts'
    __table_args__ = (UniqueConstraint('actor_id', 'operation', 'key'),)
    actor_id: Mapped[UUID] = mapped_column(ForeignKey('users.id'))
    operation: Mapped[str] = mapped_column(String(60))
    key: Mapped[str] = mapped_column(String(100))
    request_hash: Mapped[str] = mapped_column(String(64))
    response: Mapped[dict] = mapped_column(JSON)


class StockPolicy(Record, Base):
    __tablename__ = 'stock_policies'
    __table_args__ = (UniqueConstraint('facility_id', 'medicine_id'), CheckConstraint('critical_days >= 0 AND low_days >= critical_days'), CheckConstraint('lead_days >= 0 AND safety_stock >= 0'))
    facility_id: Mapped[UUID] = mapped_column(ForeignKey('facilities.id'), index=True)
    medicine_id: Mapped[UUID] = mapped_column(ForeignKey('medicines.id'), index=True)
    critical_days: Mapped[float] = mapped_column(default=3)
    low_days: Mapped[float] = mapped_column(default=7)
    lead_days: Mapped[int] = mapped_column(default=7)
    safety_stock: Mapped[int] = mapped_column(default=0)
    minimum_history_days: Mapped[int] = mapped_column(default=7)
    expiry_warning_days: Mapped[int] = mapped_column(default=90)


class RecallRecord(Record, Base):
    __tablename__ = 'recall_records'
    batch_id: Mapped[UUID] = mapped_column(ForeignKey('medicine_batches.id'), index=True)
    reason: Mapped[str] = mapped_column(String(1000))
    severity: Mapped[str] = mapped_column(String(20))
    initiated_by: Mapped[UUID] = mapped_column(ForeignKey('users.id'))
    status: Mapped[str] = mapped_column(String(30), default='active')
    resolution: Mapped[str | None] = mapped_column(String(1000))


class ExpiryRecord(Record, Base):
    __tablename__ = 'expiry_records'
    inventory_id: Mapped[UUID] = mapped_column(ForeignKey('medicine_inventory.id'), index=True)
    transaction_id: Mapped[UUID] = mapped_column(ForeignKey('stock_transactions.id'), unique=True)
    quantity: Mapped[int]
