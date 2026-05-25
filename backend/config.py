"""Central place for environment-driven configuration."""
import os

from dotenv import load_dotenv

load_dotenv()

# --- Database ---
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./es_tu_cumple.db")

# --- Kapso (WhatsApp provider) ---
# REST API base; mirrors Meta's Cloud API. The phone_number_id is appended.
KAPSO_API_BASE = os.getenv("KAPSO_API_BASE", "https://api.kapso.ai/meta/whatsapp/v24.0")
KAPSO_API_KEY = os.getenv("KAPSO_API_KEY", "")
KAPSO_PHONE_NUMBER_ID = os.getenv("KAPSO_PHONE_NUMBER_ID", "")
# Shared secret used to verify the X-Webhook-Signature header on inbound events.
KAPSO_WEBHOOK_SECRET = os.getenv("KAPSO_WEBHOOK_SECRET", "")

# --- Reminders ---
# Approved WhatsApp template used for the proactive (outside-24h) daily reminder.
REMINDER_TEMPLATE_NAME = os.getenv("REMINDER_TEMPLATE_NAME", "birthday_reminder")
REMINDER_TEMPLATE_LANG = os.getenv("REMINDER_TEMPLATE_LANG", "es")
REMINDER_HOUR = int(os.getenv("REMINDER_HOUR", "9"))
APP_TIMEZONE = os.getenv("APP_TIMEZONE", "America/Argentina/Buenos_Aires")
