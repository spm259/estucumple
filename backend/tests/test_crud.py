from datetime import date

from backend import crud, schemas


def test_get_or_create_user_is_idempotent(db):
    u1 = crud.get_or_create_user_by_phone(db, "5490000")
    u2 = crud.get_or_create_user_by_phone(db, "5490000")
    assert u1.id == u2.id


def test_contacts_with_birthday_today(db):
    user = crud.get_or_create_user_by_phone(db, "549111")
    other = crud.get_or_create_user_by_phone(db, "549222")
    crud.create_contact(
        db, user.id, schemas.ContactCreate(name="Hoy", birth_month=5, birth_day=23)
    )
    crud.create_contact(
        db, user.id, schemas.ContactCreate(name="Manana", birth_month=5, birth_day=24)
    )
    crud.create_contact(
        db, other.id, schemas.ContactCreate(name="Tambien", birth_month=5, birth_day=23)
    )

    today = crud.contacts_with_birthday_today(db, 5, 23)
    names = sorted(c.name for c in today)
    assert names == ["Hoy", "Tambien"]


def test_reminder_dedupe(db):
    user = crud.get_or_create_user_by_phone(db, "549333")
    today = date(2026, 5, 23)
    assert crud.already_reminded(db, user.id, today) is False
    crud.mark_reminded(db, user.id, today)
    assert crud.already_reminded(db, user.id, today) is True


def test_delete_scoped_to_user(db):
    user = crud.get_or_create_user_by_phone(db, "549444")
    other = crud.get_or_create_user_by_phone(db, "549555")
    c = crud.create_contact(
        db, user.id, schemas.ContactCreate(name="Mia", birth_month=1, birth_day=1)
    )
    # Another user cannot delete it.
    assert crud.delete_contact_by_id(db, other.id, c.id) is None
    assert crud.delete_contact_by_id(db, user.id, c.id) is not None
