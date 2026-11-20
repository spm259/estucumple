from datetime import date
from threading import Lock
from typing import List, Optional

from sqlalchemy.orm import Session

from . import models, schemas

# Keep the lookup and insert together for concurrent requests in this process.
_contact_creation_lock = Lock()


class DuplicateContactNameError(Exception):
    def __init__(self, contact: models.Contact) -> None:
        super().__init__("A contact with this name already exists")
        self.contact = contact


def get_or_create_user_by_phone(db: Session, phone_number: str) -> models.User:
    """Look up a user by their WhatsApp number, creating one on first contact."""
    user = (
        db.query(models.User)
        .filter(models.User.phone_number == phone_number)
        .first()
    )
    if user is None:
        user = models.User(phone_number=phone_number)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def create_contact(
    db: Session, user_id: int, contact: schemas.ContactCreate
) -> models.Contact:
    """Save a birthday or raise DuplicateContactNameError with the saved contact."""
    folded_name = contact.name.casefold()
    with _contact_creation_lock:
        existing_contacts = (
            db.query(models.Contact)
            .filter(models.Contact.user_id == user_id)
            .order_by(models.Contact.id)
        )
        # SQLite's case-insensitive matching does not cover names like MARÍA.
        for existing in existing_contacts:
            if existing.name.casefold() == folded_name:
                raise DuplicateContactNameError(existing)

        db_contact = models.Contact(
            user_id=user_id,
            name=contact.name,
            birth_month=contact.birth_month,
            birth_day=contact.birth_day,
            birth_year=contact.birth_year,
        )
        db.add(db_contact)
        db.commit()
        db.refresh(db_contact)
        return db_contact


def list_contacts(db: Session, user_id: int) -> List[models.Contact]:
    return (
        db.query(models.Contact)
        .filter(models.Contact.user_id == user_id)
        .order_by(models.Contact.birth_month, models.Contact.birth_day)
        .all()
    )


def delete_contact_by_name(
    db: Session, user_id: int, name: str
) -> Optional[models.Contact]:
    contact = (
        db.query(models.Contact)
        .filter(
            models.Contact.user_id == user_id,
            models.Contact.name.ilike(name),
        )
        .first()
    )
    if contact:
        db.delete(contact)
        db.commit()
    return contact


def delete_contact_by_id(
    db: Session, user_id: int, contact_id: int
) -> Optional[models.Contact]:
    contact = (
        db.query(models.Contact)
        .filter(
            models.Contact.user_id == user_id,
            models.Contact.id == contact_id,
        )
        .first()
    )
    if contact:
        db.delete(contact)
        db.commit()
    return contact


def contacts_with_birthday_today(
    db: Session, month: int, day: int
) -> List[models.Contact]:
    """All contacts (joined to their user) whose birthday is on month/day."""
    return (
        db.query(models.Contact)
        .join(models.User)
        .filter(
            models.Contact.birth_month == month,
            models.Contact.birth_day == day,
        )
        .all()
    )


def already_reminded(db: Session, user_id: int, sent_on: date) -> bool:
    return (
        db.query(models.ReminderLog)
        .filter(
            models.ReminderLog.user_id == user_id,
            models.ReminderLog.sent_on == sent_on,
        )
        .first()
        is not None
    )


def mark_reminded(db: Session, user_id: int, sent_on: date) -> None:
    db.add(models.ReminderLog(user_id=user_id, sent_on=sent_on))
    db.commit()
