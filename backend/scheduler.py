"""Daily job that sends birthday reminders via WhatsApp."""
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from . import config, crud, whatsapp
from .database import SessionLocal

logger = logging.getLogger(__name__)


def send_birthday_reminders() -> int:
    """Send one reminder per user with a birthday today. Returns users notified."""
    tz = ZoneInfo(config.APP_TIMEZONE)
    today = datetime.now(tz).date()

    db = SessionLocal()
    notified = 0
    try:
        contacts = crud.contacts_with_birthday_today(db, today.month, today.day)

        # Group today's birthday names by the user who should be reminded.
        by_user: dict[int, dict] = {}
        for c in contacts:
            entry = by_user.setdefault(c.user_id, {"user": c.user, "names": []})
            entry["names"].append(c.name)

        for user_id, entry in by_user.items():
            if crud.already_reminded(db, user_id, today):
                continue
            names = ", ".join(entry["names"])
            try:
                whatsapp.send_template(
                    to=entry["user"].phone_number,
                    template_name=config.REMINDER_TEMPLATE_NAME,
                    body_params=[names],
                    lang=config.REMINDER_TEMPLATE_LANG,
                )
            except Exception:  # noqa: BLE001 - keep going for other users
                logger.exception("Failed to send reminder to user %s", user_id)
                continue
            crud.mark_reminded(db, user_id, today)
            notified += 1
    finally:
        db.close()

    logger.info("Birthday reminders sent to %d user(s)", notified)
    return notified


def start_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone=ZoneInfo(config.APP_TIMEZONE))
    scheduler.add_job(
        send_birthday_reminders,
        CronTrigger(hour=config.REMINDER_HOUR, minute=0),
        id="daily_birthday_reminders",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(
        "Scheduler started: daily at %02d:00 %s",
        config.REMINDER_HOUR,
        config.APP_TIMEZONE,
    )
    return scheduler


if __name__ == "__main__":
    # Manual one-shot run for testing without waiting for the cron time.
    logging.basicConfig(level=logging.INFO)
    from .database import Base, engine

    Base.metadata.create_all(bind=engine)
    count = send_birthday_reminders()
    print(f"Sent reminders to {count} user(s).")
