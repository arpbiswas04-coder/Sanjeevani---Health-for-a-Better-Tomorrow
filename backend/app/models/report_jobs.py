from datetime import datetime
from uuid import UUID
from sqlalchemy import ForeignKey,String,DateTime,LargeBinary
from sqlalchemy.orm import Mapped,mapped_column
from app.core.database import Base
from app.models.platform import Record


class ReportJob(Record,Base):
    __tablename__='report_jobs'
    owner_id:Mapped[UUID]=mapped_column(ForeignKey('users.id'),index=True)
    facility_id:Mapped[UUID]=mapped_column(ForeignKey('facilities.id'))
    kind:Mapped[str]=mapped_column(String(30))
    format:Mapped[str]=mapped_column(String(10))
    status:Mapped[str]=mapped_column(String(30),default='pending',index=True)
    content:Mapped[bytes|None]=mapped_column(LargeBinary)
    media_type:Mapped[str|None]=mapped_column(String(100))
    failure_code:Mapped[str|None]=mapped_column(String(100))
    expires_at:Mapped[datetime]=mapped_column(DateTime(timezone=True))


class ReportSchedule(Record,Base):
    __tablename__='report_schedules'
    owner_id:Mapped[UUID]=mapped_column(ForeignKey('users.id'))
    facility_id:Mapped[UUID]=mapped_column(ForeignKey('facilities.id'))
    kind:Mapped[str]=mapped_column(String(30))
    format:Mapped[str]=mapped_column(String(10))
    interval_minutes:Mapped[int]
    next_run:Mapped[datetime]=mapped_column(DateTime(timezone=True),index=True)
    active:Mapped[bool]=mapped_column(default=True)
