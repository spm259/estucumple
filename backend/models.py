from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .database import Base


def _utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    # The WhatsApp number that both identifies the user and receives reminders.
    phone_number = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    timezone = Column(String, nullable=False, default="America/Argentina/Buenos_Aires")
    created_at = Column(DateTime, default=_utcnow)

    contacts = relationship(
        "Contact", back_populates="user", cascade="all, delete-orphan"
    )


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    name = Column(String, nullable=False)
    # Month/day stored separately so "today's birthdays" is a simple equality
    # query and the birth year can be unknown.
    birth_month = Column(Integer, nullable=False)
    birth_day = Column(Integer, nullable=False)
    birth_year = Column(Integer, nullable=True)

    user = relationship("User", back_populates="contacts")


class ReminderLog(Base):
    """One row per (user, calendar day) we sent a reminder for, to dedupe."""

    __tablename__ = "reminder_log"
    __table_args__ = (UniqueConstraint("user_id", "sent_on", name="uq_user_day"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    sent_on = Column(Date, nullable=False)
