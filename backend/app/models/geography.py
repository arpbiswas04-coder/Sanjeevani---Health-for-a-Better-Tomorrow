from uuid import UUID
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models.platform import Record


class Country(Record, Base):
    __tablename__ = 'countries'
    name: Mapped[str] = mapped_column(String(150))
    code: Mapped[str] = mapped_column(String(8), unique=True)


class State(Record, Base):
    __tablename__ = 'states'
    __table_args__ = (UniqueConstraint('country_id', 'code'),)
    country_id: Mapped[UUID] = mapped_column(ForeignKey('countries.id'), index=True)
    name: Mapped[str] = mapped_column(String(150))
    code: Mapped[str] = mapped_column(String(20))


class District(Record, Base):
    __tablename__ = 'districts'
    __table_args__ = (UniqueConstraint('state_id', 'code'),)
    state_id: Mapped[UUID] = mapped_column(ForeignKey('states.id'), index=True)
    name: Mapped[str] = mapped_column(String(150))
    code: Mapped[str] = mapped_column(String(20))


class Block(Record, Base):
    __tablename__ = 'blocks'
    __table_args__ = (UniqueConstraint('district_id', 'code'),)
    district_id: Mapped[UUID] = mapped_column(ForeignKey('districts.id'), index=True)
    name: Mapped[str] = mapped_column(String(150))
    code: Mapped[str] = mapped_column(String(20))
