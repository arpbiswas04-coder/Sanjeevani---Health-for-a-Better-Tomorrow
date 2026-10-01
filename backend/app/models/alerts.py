from datetime import datetime
from uuid import UUID
from sqlalchemy import ForeignKey,String,JSON,DateTime,UniqueConstraint
from sqlalchemy.orm import Mapped,mapped_column
from app.core.database import Base
from app.models.platform import Record


class AlertRule(Record,Base):
    __tablename__='alert_rules'
    facility_id:Mapped[UUID]=mapped_column(ForeignKey('facilities.id'),index=True)
    kind:Mapped[str]=mapped_column(String(40))
    threshold:Mapped[float]
    window_days:Mapped[int]=mapped_column(default=90)
    severity:Mapped[str]=mapped_column(String(20))
    active:Mapped[bool]=mapped_column(default=True)


class Alert(Record,Base):
    __tablename__='alerts'
    facility_id:Mapped[UUID]=mapped_column(ForeignKey('facilities.id'),index=True)
    rule_id:Mapped[UUID]=mapped_column(ForeignKey('alert_rules.id'))
    kind:Mapped[str]=mapped_column(String(40))
    severity:Mapped[str]=mapped_column(String(20))
    source:Mapped[str]=mapped_column(String(100))
    active_key:Mapped[str|None]=mapped_column(String(64),unique=True)
    status:Mapped[str]=mapped_column(String(20),default='open')
    details:Mapped[dict]=mapped_column(JSON)
    acknowledged_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True))
    resolved_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True))


class NotificationLog(Record,Base):
    __tablename__='notification_logs'
    dedup_key:Mapped[str]=mapped_column(String(200),unique=True)
    recipient_id:Mapped[UUID]=mapped_column(ForeignKey('users.id'),index=True)
    facility_id:Mapped[UUID]=mapped_column(ForeignKey('facilities.id'))
    channel:Mapped[str]=mapped_column(String(20))
    template:Mapped[str]=mapped_column(String(80))
    payload:Mapped[dict]=mapped_column(JSON)
    status:Mapped[str]=mapped_column(String(30),default='pending')
    attempts:Mapped[int]=mapped_column(default=0)
    failure_reason:Mapped[str|None]=mapped_column(String(100))
    delivered_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True))


class EscalationRule(Record,Base):
    __tablename__='escalation_rules'
    rule_id:Mapped[UUID]=mapped_column(ForeignKey('alert_rules.id'),index=True)
    after_minutes:Mapped[int]
    recipient_id:Mapped[UUID]=mapped_column(ForeignKey('users.id'))
    channel:Mapped[str]=mapped_column(String(20))
    active:Mapped[bool]=mapped_column(default=True)


class EscalationHistory(Record,Base):
    __tablename__='escalation_history'
    __table_args__=(UniqueConstraint('alert_id','escalation_rule_id'),)
    alert_id:Mapped[UUID]=mapped_column(ForeignKey('alerts.id'))
    escalation_rule_id:Mapped[UUID]=mapped_column(ForeignKey('escalation_rules.id'))
    notification_id:Mapped[UUID]=mapped_column(ForeignKey('notification_logs.id'))
