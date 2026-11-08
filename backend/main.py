import logging
from collections import deque
from contextlib import asynccontextmanager
from typing import List, Tuple

from fastapi import BackgroundTasks, Depends, FastAPI, Request, Response
from sqlalchemy.orm import Session

from . import bot, config, whatsapp
from .database import Base, engine, get_db
from .scheduler import start_scheduler

logger = logging.getLogger(__name__)

# Bounded in-memory set of recently processed idempotency keys. Resets on
# restart. Durable deduplication remains required before production launch.
_seen_keys: deque = deque(maxlen=1000)
_seen_set: set = set()


def _already_processed(key: str) -> bool:
    return bool(key) and key in _seen_set


def _mark_processed(key: str) -> None:
    if not key:
        return
    if len(_seen_keys) == _seen_keys.maxlen:
        _seen_set.discard(_seen_keys[0])
    _seen_keys.append(key)
    _seen_set.add(key)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    scheduler = start_scheduler() if config.ENABLE_REMINDERS else None
    try:
        yield
    finally:
        if scheduler is not None:
            scheduler.shutdown(wait=False)


app = FastAPI(title="Es tu Cumple", lifespan=lifespan)


@app.get("/")
def read_root():
    return {"status": "ok", "service": "es-tu-cumple"}


def _text_message(message: object, conversation: object = None) -> List[Tuple[str, str]]:
    """Extract only actionable inbound text with a real phone destination."""
    if not isinstance(message, dict):
        return []
    if message.get("type", "text") != "text":
        return []
    kapso = message.get("kapso")
    if isinstance(kapso, dict):
        if kapso.get("direction", "inbound") != "inbound" or kapso.get("passive"):
            return []

    sender = message.get("from") or message.get("phone_number") or message.get("sender")
    if not sender and isinstance(conversation, dict):
        sender = conversation.get("phone_number")
    # BSUIDs and usernames are not phone numbers. Do not guess a destination.
    if not isinstance(sender, str):
        return []
    sender = sender.strip().lstrip("+")
    if not sender or not sender.isascii() or not sender.isdigit():
        return []

    text = message.get("text")
    if isinstance(text, dict):
        text = text.get("body")
    if text is None:
        text = message.get("body")
    if text is None and isinstance(message.get("message"), str):
        text = message["message"]  # Legacy flattened payload.
    if not isinstance(text, str) or not text.strip():
        return []
    return [(sender, text)]


def extract_messages(payload: object) -> List[Tuple[str, str]]:
    """Handle Kapso v2, buffered v2, forwarded Meta, and legacy flat text."""
    if not isinstance(payload, dict):
        return []

    if payload.get("batch") is True:
        data = payload.get("data")
        if not isinstance(data, list):
            return []
        return [message for item in data for message in extract_messages(item)]

    if "message" in payload and isinstance(payload["message"], dict):
        return _text_message(payload["message"], payload.get("conversation"))

    messages: List[Tuple[str, str]] = []
    # Meta-style: entry[].changes[].value.messages[]
    entries = payload.get("entry")
    if isinstance(entries, list):
        for entry in entries:
            changes = entry.get("changes") if isinstance(entry, dict) else None
            if not isinstance(changes, list):
                continue
            for change in changes:
                value = change.get("value") if isinstance(change, dict) else None
                batch = value.get("messages") if isinstance(value, dict) else None
                if isinstance(batch, list):
                    for msg in batch:
                        messages.extend(_text_message(msg))
        return messages

    # Older Kapso shapes. Malformed/non-text payloads are ignored.
    data = payload.get("data", payload)
    return _text_message(data)


def send_reply(sender: str, reply: str) -> None:
    """Send after acknowledgment; these local background tasks are not durable."""
    try:
        whatsapp.send_text(sender, reply)
    except Exception:  # noqa: BLE001
        logger.exception("Failed to send WhatsApp reply")


@app.post("/webhooks/whatsapp")
async def whatsapp_webhook(
    request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)
):
    raw = await request.body()

    if not config.KAPSO_WEBHOOK_SECRET:
        logger.error("KAPSO_WEBHOOK_SECRET unset; refusing webhook")
        return Response(status_code=503)
    signature = request.headers.get("X-Webhook-Signature", "")
    if not whatsapp.verify_signature(raw, signature):
        return Response(status_code=403)

    event = request.headers.get("X-Webhook-Event")
    if event and event != "whatsapp.message.received":
        return {"status": "ignored", "event": event}

    try:
        payload = await request.json()
    except Exception:  # noqa: BLE001
        return {"status": "ignored", "reason": "invalid json"}

    messages = extract_messages(payload)
    if not messages:
        return {"status": "ignored", "reason": "no supported phone-based text"}

    key = request.headers.get("X-Idempotency-Key", "")
    if _already_processed(key):
        return {"status": "duplicate"}

    for sender, text in messages:
        reply = bot.handle_message(db, sender, text)
        background_tasks.add_task(send_reply, sender, reply)

    _mark_processed(key)
    return {"status": "ok"}
