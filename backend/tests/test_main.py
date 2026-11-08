import hashlib
import hmac
import json
from unittest.mock import Mock

import pytest
from fastapi import BackgroundTasks
from fastapi.testclient import TestClient
from starlette.requests import Request

from backend import config, crud, main, models, whatsapp


SECRET = "test-webhook-secret"
PHONE = "525500001111"


def received(text="agregar María 25/05", phone=PHONE):
    return {
        "message": {
            "id": "wamid.test",
            "type": "text",
            "from": phone,
            "text": {"body": text},
            "kapso": {"direction": "inbound"},
        },
        "conversation": {"phone_number": phone},
        "phone_number_id": "test-number-id",
    }


def signature(raw):
    return hmac.new(SECRET.encode(), raw, hashlib.sha256).hexdigest()


@pytest.fixture
def webhook(db, monkeypatch):
    monkeypatch.setattr(config, "KAPSO_WEBHOOK_SECRET", SECRET)
    main._seen_keys.clear()
    main._seen_set.clear()
    main.app.dependency_overrides[main.get_db] = lambda: db
    replies = []
    monkeypatch.setattr(whatsapp, "send_text", lambda to, body: replies.append((to, body)))
    client = TestClient(main.app)
    yield client, replies
    client.close()
    main.app.dependency_overrides.clear()
    main._seen_keys.clear()
    main._seen_set.clear()


def post(client, payload, **headers):
    # Sign the exact Unicode bytes sent over HTTP.
    raw = json.dumps(payload, ensure_ascii=False).encode()
    return client.post(
        "/webhooks/whatsapp",
        content=raw,
        headers={
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature(raw),
            "X-Webhook-Event": "whatsapp.message.received",
            **headers,
        },
    )


def test_signed_kapso_v2_spanish_conversation(webhook, db):
    client, replies = webhook
    for command in ["hola", "agregar María 25/05", "lista", "borrar María", "lista"]:
        response = post(client, received(command))
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
    assert "Es tu Cumple" in replies[0][1]
    assert "Guardado: María — 25/05" in replies[1][1]
    assert "María — 25/05" in replies[2][1]
    assert "Eliminado: María" in replies[3][1]
    assert "no tienes cumpleaños" in replies[4][1]
    assert all(to == PHONE for to, _ in replies)
    assert db.query(models.Contact).count() == 0


def test_buffered_kapso_batch_stays_scoped_to_each_user(webhook, db):
    client, replies = webhook
    payload = {"batch": True, "data": [received(), received("lista", "525500002222")]}
    assert post(client, payload).json() == {"status": "ok"}
    assert len(replies) == 2
    assert "María" in replies[0][1]
    assert "Todavía no tienes cumpleaños guardados" in replies[1][1]
    other = crud.get_or_create_user_by_phone(db, "525500002222")
    assert crud.list_contacts(db, other.id) == []
    assert db.query(models.Contact).count() == 1


def test_duplicate_event_does_not_repeat_command_or_reply(webhook, db):
    client, replies = webhook
    headers = {"X-Idempotency-Key": "duplicate-test"}
    assert post(client, received(), **headers).json()["status"] == "ok"
    assert post(client, received(), **headers).json()["status"] == "duplicate"
    assert db.query(models.Contact).count() == 1
    assert len(replies) == 1


@pytest.mark.parametrize("bad_signature", ["", "forged", "0" * 64])
def test_invalid_signature_cannot_write_or_reply(webhook, db, bad_signature):
    client, replies = webhook
    response = post(client, received(), **{"X-Webhook-Signature": bad_signature})
    assert response.status_code == 403
    assert db.query(models.User).count() == 0
    assert replies == []


def test_missing_secret_fails_closed(webhook, db, monkeypatch):
    client, replies = webhook
    monkeypatch.setattr(config, "KAPSO_WEBHOOK_SECRET", "")
    assert post(client, received()).status_code == 503
    assert db.query(models.User).count() == 0
    assert replies == []


def test_non_received_events_are_ignored(webhook, db):
    client, replies = webhook
    response = post(client, received(), **{"X-Webhook-Event": "whatsapp.message.sent"})
    assert response.json()["status"] == "ignored"
    assert db.query(models.User).count() == 0
    assert replies == []


def test_invalid_json_does_not_consume_idempotency_key(webhook):
    client, replies = webhook
    raw = b"not json"
    response = client.post(
        "/webhooks/whatsapp",
        content=raw,
        headers={"X-Webhook-Signature": signature(raw), "X-Idempotency-Key": "retry"},
    )
    assert response.json()["reason"] == "invalid json"
    assert post(client, received(), **{"X-Idempotency-Key": "retry"}).json()["status"] == "ok"
    assert len(replies) == 1


def test_failed_command_does_not_consume_idempotency_key(webhook, monkeypatch):
    client, replies = webhook
    handler = main.bot.handle_message
    monkeypatch.setattr(main.bot, "handle_message", Mock(side_effect=RuntimeError("db failed")))
    with pytest.raises(RuntimeError, match="db failed"):
        post(client, received(), **{"X-Idempotency-Key": "failed-command"})
    monkeypatch.setattr(main.bot, "handle_message", handler)
    assert post(client, received(), **{"X-Idempotency-Key": "failed-command"}).json()["status"] == "ok"
    assert len(replies) == 1


@pytest.mark.parametrize("payload", [None, [], "text", {}, {"batch": True, "data": {}},
    {"entry": [None, {"changes": [None, {"value": None}]}]},
    {"data": [None]}, {"message": {"from": 123, "text": {"body": "lista"}}}])
def test_malformed_payloads_are_ignored_without_mutation(webhook, db, payload):
    client, replies = webhook
    response = post(client, payload)
    assert response.status_code == 200
    assert response.json()["status"] == "ignored"
    assert db.query(models.User).count() == 0
    assert replies == []


def test_bsuid_without_phone_is_not_used_as_a_reply_destination(webhook, db):
    client, replies = webhook
    payload = received(phone=None)
    payload["message"]["from_user_id"] = "US.123456"
    payload["conversation"]["business_scoped_user_id"] = "US.123456"
    assert post(client, payload).json()["status"] == "ignored"
    assert db.query(models.User).count() == 0
    assert replies == []


def test_v2_can_use_conversation_phone_if_from_is_missing():
    payload = received()
    del payload["message"]["from"]
    assert main.extract_messages(payload) == [(PHONE, "agregar María 25/05")]


def test_meta_forwarded_payload():
    payload = {"entry": [{"changes": [{"value": {"messages": [received()["message"]]}}]}]}
    assert main.extract_messages(payload) == [(PHONE, "agregar María 25/05")]


@pytest.mark.parametrize("payload", [
    {"from": PHONE, "text": {"body": "lista"}},
    {"data": {"phone_number": PHONE, "text": "lista"}},
    {"sender": PHONE, "message": "lista"},
])
def test_legacy_flattened_payloads(payload):
    assert main.extract_messages(payload) == [(PHONE, "lista")]


@pytest.mark.parametrize("change", [
    {"type": "image"},
    {"kapso": {"direction": "outbound"}},
    {"kapso": {"passive": True}},
    {"text": {"body": "   "}},
    {"from": "US.123456"},
])
def test_non_actionable_messages_are_ignored(change):
    payload = received()
    payload["message"].update(change)
    assert main.extract_messages(payload) == []


@pytest.mark.anyio
async def test_reply_is_deferred_until_after_acknowledgment(webhook, db):
    _, replies = webhook
    raw = json.dumps(received()).encode()

    async def receive():
        return {"type": "http.request", "body": raw, "more_body": False}

    request = Request({"type": "http", "headers": [
        (b"x-webhook-signature", signature(raw).encode())]}, receive)
    tasks = BackgroundTasks()
    assert await main.whatsapp_webhook(request, tasks, db) == {"status": "ok"}
    assert db.query(models.Contact).count() == 1
    assert replies == []
    await tasks()
    assert len(replies) == 1


def test_failed_reply_does_not_reapply_saved_command(webhook, db, monkeypatch, caplog):
    client, _ = webhook
    monkeypatch.setattr(whatsapp, "send_text", Mock(side_effect=RuntimeError("send failed")))
    headers = {"X-Idempotency-Key": "failed-reply"}
    assert post(client, received(), **headers).json()["status"] == "ok"
    assert post(client, received(), **headers).json()["status"] == "duplicate"
    assert db.query(models.Contact).count() == 1
    assert "Failed to send WhatsApp reply" in caplog.text


@pytest.mark.parametrize("enabled", [False, True])
def test_scheduler_is_optional_for_sandbox(db, monkeypatch, enabled):
    scheduler = Mock()
    start = Mock(return_value=scheduler)
    monkeypatch.setattr(config, "ENABLE_REMINDERS", enabled)
    monkeypatch.setattr(main, "engine", db.get_bind())
    monkeypatch.setattr(main, "start_scheduler", start)
    with TestClient(main.app) as client:
        assert client.get("/").json()["status"] == "ok"
    assert start.call_count == int(enabled)
    assert scheduler.shutdown.call_count == int(enabled)
