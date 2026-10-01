from datetime import datetime
from decimal import Decimal
from uuid import UUID
from sqlalchemy import ForeignKey, String, Numeric, DateTime, JSON, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models.platform import Record


class Supplier(Record, Base):
    __tablename__ = 'suppliers'
    name: Mapped[str] = mapped_column(String(200))
    code: Mapped[str] = mapped_column(String(50), unique=True)
    contact: Mapped[str | None] = mapped_column(String(200))
    address: Mapped[str | None] = mapped_column(String(500))
    active: Mapped[bool] = mapped_column(default=True)
    lead_days: Mapped[int] = mapped_column(default=7)


class Warehouse(Record, Base):
    __tablename__ = 'warehouses'
    facility_id: Mapped[UUID] = mapped_column(ForeignKey('facilities.id'), unique=True)
    capacity: Mapped[dict] = mapped_column(JSON, default=dict)
    active: Mapped[bool] = mapped_column(default=True)


class WarehouseInventory(Record, Base):
    __tablename__ = 'warehouse_inventory'
    warehouse_id: Mapped[UUID] = mapped_column(ForeignKey('warehouses.id'), index=True)
    inventory_id: Mapped[UUID] = mapped_column(ForeignKey('medicine_inventory.id'), unique=True)


class PurchaseOrder(Record, Base):
    __tablename__ = 'purchase_orders'
    reference: Mapped[str] = mapped_column(String(100), unique=True)
    supplier_id: Mapped[UUID] = mapped_column(ForeignKey('suppliers.id'), index=True)
    facility_id: Mapped[UUID] = mapped_column(ForeignKey('facilities.id'), index=True)
    status: Mapped[str] = mapped_column(String(30), default='draft')
    created_by: Mapped[UUID] = mapped_column(ForeignKey('users.id'))


class PurchaseOrderItem(Record, Base):
    __tablename__ = 'purchase_order_items'
    __table_args__ = (UniqueConstraint('order_id','medicine_id'), CheckConstraint('quantity > 0 AND received >= 0 AND received <= quantity'), CheckConstraint('unit_price >= 0'))
    order_id: Mapped[UUID] = mapped_column(ForeignKey('purchase_orders.id'), index=True)
    medicine_id: Mapped[UUID] = mapped_column(ForeignKey('medicines.id'))
    quantity: Mapped[int]
    received: Mapped[int] = mapped_column(default=0)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14,2))


class ProcurementHistory(Record, Base):
    __tablename__ = 'procurement_history'
    order_id: Mapped[UUID] = mapped_column(ForeignKey('purchase_orders.id'), index=True)
    actor_id: Mapped[UUID] = mapped_column(ForeignKey('users.id'))
    status: Mapped[str] = mapped_column(String(30))
    note: Mapped[str] = mapped_column(String(500))


class Shipment(Record, Base):
    __tablename__ = 'shipments'
    __table_args__ = (CheckConstraint('(order_id IS NULL) <> (transfer_id IS NULL)'),)
    reference: Mapped[str] = mapped_column(String(100), unique=True)
    order_id: Mapped[UUID | None] = mapped_column(ForeignKey('purchase_orders.id'), index=True)
    transfer_id: Mapped[UUID | None] = mapped_column(ForeignKey('transfer_requests.id'), index=True)
    supplier_id: Mapped[UUID | None] = mapped_column(ForeignKey('suppliers.id'))
    facility_id: Mapped[UUID] = mapped_column(ForeignKey('facilities.id'), index=True)
    origin: Mapped[str] = mapped_column(String(200))
    transport: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(30), default='planned')
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    arrived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ShipmentHistory(Record, Base):
    __tablename__ = 'shipment_history'
    shipment_id: Mapped[UUID] = mapped_column(ForeignKey('shipments.id'), index=True)
    actor_id: Mapped[UUID] = mapped_column(ForeignKey('users.id'))
    status: Mapped[str] = mapped_column(String(30))
    note: Mapped[str] = mapped_column(String(500))
