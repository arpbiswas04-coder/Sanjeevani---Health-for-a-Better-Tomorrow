from datetime import date,datetime
from uuid import UUID
from sqlalchemy import ForeignKey,String,DateTime,UniqueConstraint,CheckConstraint,Index
from sqlalchemy.orm import Mapped,mapped_column
from app.core.database import Base
from app.models.platform import Record


class TemperatureObservation(Record,Base):
    __tablename__='temperature_observations'
    __table_args__=(UniqueConstraint('source','external_id'),CheckConstraint('minimum < maximum'))
    facility_id:Mapped[UUID]=mapped_column(ForeignKey('facilities.id'),index=True)
    shipment_id:Mapped[UUID|None]=mapped_column(ForeignKey('shipments.id'))
    observed_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),index=True)
    temperature:Mapped[float]
    minimum:Mapped[float]
    maximum:Mapped[float]
    source:Mapped[str]=mapped_column(String(100))
    external_id:Mapped[str]=mapped_column(String(100))
    excursion:Mapped[bool]


class BedCapacity(Record,Base):
    __tablename__='bed_capacity'
    __table_args__=(UniqueConstraint('facility_id','bed_type'),CheckConstraint('capacity >= 0 AND occupied >= 0 AND occupied <= capacity'))
    facility_id:Mapped[UUID]=mapped_column(ForeignKey('facilities.id'),index=True)
    bed_type:Mapped[str]=mapped_column(String(50))
    capacity:Mapped[int]
    occupied:Mapped[int]


class BedOccupancyHistory(Record,Base):
    __tablename__='bed_occupancy_history'
    bed_id:Mapped[UUID]=mapped_column(ForeignKey('bed_capacity.id'),index=True)
    capacity:Mapped[int]
    occupied:Mapped[int]
    actor_id:Mapped[UUID]=mapped_column(ForeignKey('users.id'))


class StaffRole(Record,Base):
    __tablename__='staff_roles'
    name:Mapped[str]=mapped_column(String(100),unique=True)


class Staff(Record,Base):
    __tablename__='staff'
    facility_id:Mapped[UUID]=mapped_column(ForeignKey('facilities.id'),index=True)
    staff_role_id:Mapped[UUID]=mapped_column(ForeignKey('staff_roles.id'))
    code:Mapped[str]=mapped_column(String(50),unique=True)
    display_name:Mapped[str]=mapped_column(String(200))
    active:Mapped[bool]=mapped_column(default=True)


class Shift(Record,Base):
    __tablename__='shifts'
    __table_args__=(CheckConstraint('ends_at > starts_at'),)
    staff_id:Mapped[UUID]=mapped_column(ForeignKey('staff.id'),index=True)
    facility_id:Mapped[UUID]=mapped_column(ForeignKey('facilities.id'),index=True)
    starts_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),index=True)
    ends_at:Mapped[datetime]=mapped_column(DateTime(timezone=True))
    cancelled:Mapped[bool]=mapped_column(default=False)


class Attendance(Record,Base):
    __tablename__='attendance'
    __table_args__=(UniqueConstraint('staff_id','day'),)
    staff_id:Mapped[UUID]=mapped_column(ForeignKey('staff.id'),index=True)
    facility_id:Mapped[UUID]=mapped_column(ForeignKey('facilities.id'),index=True)
    day:Mapped[date]
    status:Mapped[str]=mapped_column(String(30))


class PatientFootfall(Record,Base):
    __tablename__='patient_footfall_aggregates'
    __table_args__=(UniqueConstraint('facility_id','day','category'),CheckConstraint('count >= 0'))
    facility_id:Mapped[UUID]=mapped_column(ForeignKey('facilities.id'),index=True)
    day:Mapped[date]=mapped_column(index=True)
    category:Mapped[str]=mapped_column(String(100))
    count:Mapped[int]
    version:Mapped[int]=mapped_column(default=1)
    source_device:Mapped[str|None]=mapped_column(String(100))


class DiseaseCount(Record,Base):
    __tablename__='disease_counts'
    __table_args__=(UniqueConstraint('facility_id','day','category'),CheckConstraint('count >= 0'))
    facility_id:Mapped[UUID]=mapped_column(ForeignKey('facilities.id'),index=True)
    day:Mapped[date]=mapped_column(index=True)
    category:Mapped[str]=mapped_column(String(100))
    count:Mapped[int]
    version:Mapped[int]=mapped_column(default=1)
    source_device:Mapped[str|None]=mapped_column(String(100))


class ColdChainSample(Record,Base):
    """Rebuildable telemetry projection; observation registry owns identity/FKs."""
    __tablename__='cold_chain_samples'
    observed_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),primary_key=True)
    facility_id:Mapped[UUID]
    temperature:Mapped[float]
    minimum:Mapped[float]
    maximum:Mapped[float]
    excursion:Mapped[bool]
    __table_args__=(Index('ix_cold_chain_samples_facility_time','facility_id','observed_at'),)
