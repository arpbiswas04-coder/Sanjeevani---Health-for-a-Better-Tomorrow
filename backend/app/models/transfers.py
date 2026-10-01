from uuid import UUID
from sqlalchemy import ForeignKey, String, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models.platform import Record


class TransferRequest(Record, Base):
    __tablename__ = 'transfer_requests'
    __table_args__ = (CheckConstraint('source_id <> destination_id'),)
    source_id: Mapped[UUID] = mapped_column(ForeignKey('facilities.id'), index=True)
    destination_id: Mapped[UUID] = mapped_column(ForeignKey('facilities.id'), index=True)
    requested_by: Mapped[UUID] = mapped_column(ForeignKey('users.id'))
    status: Mapped[str] = mapped_column(String(30), default='pending_approval')
    reference: Mapped[str] = mapped_column(String(200))


class TransferItem(Record, Base):
    __tablename__ = 'transfer_items'
    __table_args__ = (CheckConstraint('quantity > 0'), UniqueConstraint('transfer_id', 'batch_id'))
    transfer_id: Mapped[UUID] = mapped_column(ForeignKey('transfer_requests.id'), index=True)
    batch_id: Mapped[UUID] = mapped_column(ForeignKey('medicine_batches.id'))
    quantity: Mapped[int]


class TransferApproval(Record, Base):
    __tablename__ = 'transfer_approvals'
    transfer_id: Mapped[UUID] = mapped_column(ForeignKey('transfer_requests.id'), index=True)
    actor_id: Mapped[UUID] = mapped_column(ForeignKey('users.id'))
    decision: Mapped[str] = mapped_column(String(30))
    reason: Mapped[str] = mapped_column(String(500))


class TransferTracking(Record, Base):
    __tablename__ = 'transfer_tracking'
    transfer_id: Mapped[UUID] = mapped_column(ForeignKey('transfer_requests.id'), index=True)
    actor_id: Mapped[UUID] = mapped_column(ForeignKey('users.id'))
    status: Mapped[str] = mapped_column(String(30))
    note: Mapped[str] = mapped_column(String(500))
