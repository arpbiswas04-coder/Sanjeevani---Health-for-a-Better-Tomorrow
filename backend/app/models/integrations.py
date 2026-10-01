from datetime import date,datetime
from uuid import UUID
from sqlalchemy import ForeignKey,String,JSON,DateTime,CheckConstraint
from sqlalchemy.orm import Mapped,mapped_column
from app.core.database import Base
from app.models.platform import Record


class Recommendation(Record,Base):
    __tablename__='optimization_recommendations'
    source_id:Mapped[UUID]=mapped_column(ForeignKey('facilities.id'),index=True)
    destination_id:Mapped[UUID]=mapped_column(ForeignKey('facilities.id'),index=True)
    submitted_by:Mapped[UUID]=mapped_column(ForeignKey('users.id'))
    status:Mapped[str]=mapped_column(String(30),default='proposed')
    payload:Mapped[dict]=mapped_column(JSON)
    model_version:Mapped[str]=mapped_column(String(100))
    transfer_id:Mapped[UUID|None]=mapped_column(ForeignKey('transfer_requests.id'))


class PopulationSnapshot(Record,Base):
    __tablename__='population_snapshots'
    __table_args__=(CheckConstraint('population >= 0'),)
    district_id:Mapped[UUID]=mapped_column(ForeignKey('districts.id'),index=True)
    population:Mapped[int]
    source:Mapped[str]=mapped_column(String(200))
    source_url:Mapped[str]=mapped_column(String(1000))
    as_of:Mapped[date]
    retrieved_at:Mapped[datetime]=mapped_column(DateTime(timezone=True))


class WeatherCache(Record,Base):
    __tablename__='weather_cache'
    facility_id:Mapped[UUID]=mapped_column(ForeignKey('facilities.id'),unique=True)
    latitude:Mapped[float]
    longitude:Mapped[float]
    retrieved_at:Mapped[datetime]=mapped_column(DateTime(timezone=True))
    payload:Mapped[dict]=mapped_column(JSON)


class Barcode(Record,Base):
    __tablename__='barcodes'
    __table_args__=(CheckConstraint('(medicine_id IS NULL) <> (batch_id IS NULL)'),)
    code:Mapped[str]=mapped_column(String(128),unique=True)
    medicine_id:Mapped[UUID|None]=mapped_column(ForeignKey('medicines.id'))
    batch_id:Mapped[UUID|None]=mapped_column(ForeignKey('medicine_batches.id'))


class BackupRecord(Record,Base):
    __tablename__='backup_records'
    artifact_key:Mapped[str]=mapped_column(String(200),unique=True)
    status:Mapped[str]=mapped_column(String(30))
    checksum:Mapped[str|None]=mapped_column(String(64))
    size_bytes:Mapped[int]
    started_at:Mapped[datetime]=mapped_column(DateTime(timezone=True))
    completed_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True))
    verified_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True))
