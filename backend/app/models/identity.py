from datetime import datetime
from uuid import UUID
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models.platform import Record


class AuthSession(Record, Base):
    __tablename__ = 'auth_sessions'
    user_id: Mapped[UUID] = mapped_column(ForeignKey('users.id'), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked: Mapped[bool] = mapped_column(default=False)


class PasswordReset(Record, Base):
    __tablename__ = 'password_resets'
    user_id: Mapped[UUID] = mapped_column(ForeignKey('users.id'), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used: Mapped[bool] = mapped_column(default=False)


class UserFacility(Base):
    __tablename__ = 'user_facilities'
    user_id: Mapped[UUID] = mapped_column(ForeignKey('users.id'), primary_key=True)
    facility_id: Mapped[UUID] = mapped_column(ForeignKey('facilities.id'), primary_key=True)

class UserDistrict(Base):
    __tablename__ = 'user_districts'
    user_id: Mapped[UUID] = mapped_column(ForeignKey('users.id'), primary_key=True)
    district_id: Mapped[UUID] = mapped_column(ForeignKey('districts.id'), primary_key=True)
