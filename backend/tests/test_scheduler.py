from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import config, crud, schemas, scheduler, whatsapp
from backend.database import Base


def test_send_birthday_reminders_and_dedupe(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    monkeypatch.setattr(scheduler, "SessionLocal", TestingSession)

    sent = []
    monkeypatch.setattr(whatsapp, "send_template", lambda **kw: sent.append(kw))

    today = datetime.now(ZoneInfo(config.APP_TIMEZONE)).date()
    db = TestingSession()
    user = crud.get_or_create_user_by_phone(db, "549999")
    crud.create_contact(
        db,
        user.id,
        schemas.ContactCreate(
            name="HoyCumple", birth_month=today.month, birth_day=today.day
        ),
    )
    db.close()

    assert scheduler.send_birthday_reminders() == 1
    assert len(sent) == 1
    assert "HoyCumple" in sent[0]["body_params"][0]

    # Second run the same day must not re-send.
    assert scheduler.send_birthday_reminders() == 0
    assert len(sent) == 1
