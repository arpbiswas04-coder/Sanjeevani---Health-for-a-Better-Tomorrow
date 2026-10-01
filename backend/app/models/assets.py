from datetime import date
from uuid import UUID
from sqlalchemy import ForeignKey,String
from sqlalchemy.orm import Mapped,mapped_column
from app.core.database import Base
from app.models.platform import Record


class Equipment(Record,Base):
    __tablename__='equipment'
    facility_id:Mapped[UUID]=mapped_column(ForeignKey('facilities.id'),index=True)
    code:Mapped[str]=mapped_column(String(80),unique=True)
    equipment_type:Mapped[str]=mapped_column(String(100))
    status:Mapped[str]=mapped_column(String(30))
    last_maintenance:Mapped[date|None]
    next_maintenance:Mapped[date|None]=mapped_column(index=True)
    notes:Mapped[str|None]=mapped_column(String(1000))


class MaintenanceRecord(Record,Base):
    __tablename__='maintenance_records'
    equipment_id:Mapped[UUID]=mapped_column(ForeignKey('equipment.id'),index=True)
    performed_on:Mapped[date]
    next_due:Mapped[date]
    notes:Mapped[str]=mapped_column(String(1000))
    actor_id:Mapped[UUID]=mapped_column(ForeignKey('users.id'))


class Ambulance(Record,Base):
    __tablename__='ambulance_records'
    facility_id:Mapped[UUID]=mapped_column(ForeignKey('facilities.id'),index=True)
    vehicle_id:Mapped[str]=mapped_column(String(80),unique=True)
    status:Mapped[str]=mapped_column(String(30))
    operational:Mapped[bool]=mapped_column(default=True)
    latitude:Mapped[float|None]
    longitude:Mapped[float|None]
