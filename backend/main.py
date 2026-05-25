import logging
from collections import deque
from contextlib import asynccontextmanager
from typing import List, Tuple

from fastapi import Depends, FastAPI, Request, Response
from sqlalchemy.orm import Session

from . import bot, config, whatsapp
from .database import Base, engine, get_db
from .scheduler import start_scheduler

logger = logging.getLogger(__name__)

# Bounded in-memory set of recently processed idempotency keys. Resets on
# restart, which is fine: WhatsApp commands are cheap to reprocess.
_seen_keys: deque = deque(maxlen=1000)
_seen_set: set = set()


def _already_processed(key: str) -> bool:
    if not key:
        return False
    if key in _seen_set:
        return True
    if len(_seen_keys) == _seen_keys.maxlen:
        _seen_set.discard(_seen_keys[0])
    _seen_keys.append(key)
    _seen_set.add(key)
    return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    scheduler = start_scheduler()
    try:
        yield
    finally:
        scheduler.shutdown(wait=False)


app = FastAPI(title="Recordatorio de Cumpleaños", lifespan=lifespan)


@app.get("/")
def read_root():
    return {"status": "ok", "service": "es-tu-cumple"}


def extract_messages(payload: dict) -> List[Tuple[str, str]]:
    """Pull (from_phone, text) pairs out of an inbound webhook payload.

    Handles the Meta-style nested shape and a flattened Kapso shape. Confirm
    against a real Kapso event and prune the branch you don't need.
    """
    messages: List[Tuple[str, str]] = []

    # Meta-style: entry[].changes[].value.messages[]
    for entry in payload.get("entry", []) or []:
        for change in entry.get("changes", []) or []:
            value = change.get("value", {}) or {}
            for msg in value.get("messages", []) or []:
                sender = msg.get("from")
                text = (msg.get("text") or {}).get("body")
                if sender and text:
                    messages.append((sender, text))

    if messages:
        return messages

    # Flattened fallback: look for sender + text under common key names.
    data = payload.get("data", payload)
    sender = data.get("from") or data.get("phone_number") or data.get("sender")
    text = data.get("text")
    if isinstance(text, dict):
        text = text.get("body")
    text = text or data.get("body") or data.get("message")
    if sender and isinstance(text, str):
        messages.append((sender, text))

    return messages


@app.post("/webhooks/whatsapp")
async def whatsapp_webhook(request: Request, db: Session = Depends(get_db)):
    raw = await request.body()

    if config.KAPSO_WEBHOOK_SECRET:
        signature = request.headers.get("X-Webhook-Signature", "")
        if not whatsapp.verify_signature(raw, signature):
            return Response(status_code=403)
    else:
        logger.warning("KAPSO_WEBHOOK_SECRET unset; skipping signature check")

    event = request.headers.get("X-Webhook-Event")
    if event and event != "whatsapp.message.received":
        return {"status": "ignored", "event": event}

    if _already_processed(request.headers.get("X-Idempotency-Key", "")):
        return {"status": "duplicate"}

    try:
        payload = await request.json()
    except Exception:  # noqa: BLE001
        return {"status": "ignored", "reason": "invalid json"}

    for sender, text in extract_messages(payload):
        reply = bot.handle_message(db, sender, text)
        try:
            whatsapp.send_text(sender, reply)
        except Exception:  # noqa: BLE001 - don't trigger provider retries
            logger.exception("Failed to send reply to %s", sender)

    return {"status": "ok"}
