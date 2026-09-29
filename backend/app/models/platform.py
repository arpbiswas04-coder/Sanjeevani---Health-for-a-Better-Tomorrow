from datetime import date, datetime, timezone
from uuid import UUID, uuid4
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Record:
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class User(Record, Base):
    __tablename__ = 'users'
    username: Mapped[str] = mapped_column(String(120), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    active: Mapped[bool] = mapped_column(default=True)


class Role(Record, Base):
    __tablename__ = 'roles'
    name: Mapped[str] = mapped_column(String(80), unique=True)


class Permission(Record, Base):
    __tablename__ = 'permissions'
    name: Mapped[str] = mapped_column(String(80), unique=True)


class UserRole(Base):
    __tablename__ = 'user_roles'
    user_id: Mapped[UUID] = mapped_column(ForeignKey('users.id'), primary_key=True)
    role_id: Mapped[UUID] = mapped_column(ForeignKey('roles.id'), primary_key=True)


class RolePermission(Base):
    __tablename__ = 'role_permissions'
    role_id: Mapped[UUID] = mapped_column(ForeignKey('roles.id'), primary_key=True)
    permission_id: Mapped[UUID] = mapped_column(ForeignKey('permissions.id'), primary_key=True)


class Facility(Record, Base):
    __tablename__ = 'facilities'
    name: Mapped[str] = mapped_column(String(200))
    code: Mapped[str] = mapped_column(String(50), unique=True)
    active: Mapped[bool] = mapped_column(default=True)


class Medicine(Record, Base):
    __tablename__ = 'medicines'
    name: Mapped[str] = mapped_column(String(200))
    code: Mapped[str] = mapped_column(String(50), unique=True)
    unit: Mapped[str] = mapped_column(String(50))


class MedicineBatch(Record, Base):
    __tablename__ = 'medicine_batches'
    __table_args__ = (UniqueConstraint('medicine_id', 'batch_number'),)
    medicine_id: Mapped[UUID] = mapped_column(ForeignKey('medicines.id'), index=True)
    batch_number: Mapped[str] = mapped_column(String(100))
    expires_on: Mapped[date] = mapped_column(index=True)
    recalled: Mapped[bool] = mapped_column(default=False)


class Inventory(Record, Base):
    __tablename__ = 'medicine_inventory'
    __table_args__ = (UniqueConstraint('facility_id', 'batch_id'), CheckConstraint('quantity >= 0'))
    facility_id: Mapped[UUID] = mapped_column(ForeignKey('facilities.id'), index=True)
    batch_id: Mapped[UUID] = mapped_column(ForeignKey('medicine_batches.id'), index=True)
    quantity: Mapped[int] = mapped_column(default=0)


class StockTransaction(Record, Base):
    __tablename__ = 'stock_transactions'
    __table_args__ = (CheckConstraint('quantity <> 0'),)
    inventory_id: Mapped[UUID] = mapped_column(ForeignKey('medicine_inventory.id'), index=True)
    actor_id: Mapped[UUID] = mapped_column(ForeignKey('users.id'))
    quantity: Mapped[int]
    kind: Mapped[str] = mapped_column(String(30))
    reference: Mapped[str] = mapped_column(String(200))


class AuditLog(Record, Base):
    __tablename__ = 'audit_logs'
    actor_id: Mapped[UUID] = mapped_column(ForeignKey('users.id'), index=True)
    action: Mapped[str] = mapped_column(String(100))
    details: Mapped[dict] = mapped_column(JSON)
