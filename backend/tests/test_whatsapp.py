import hashlib
import hmac

from backend import config, whatsapp


def _sign(secret: str, body: bytes) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def test_verify_signature_valid(monkeypatch):
    monkeypatch.setattr(config, "KAPSO_WEBHOOK_SECRET", "s3cr3t")
    body = b'{"hello":"world"}'
    assert whatsapp.verify_signature(body, _sign("s3cr3t", body)) is True


def test_verify_signature_accepts_sha256_prefix(monkeypatch):
    monkeypatch.setattr(config, "KAPSO_WEBHOOK_SECRET", "s3cr3t")
    body = b"payload"
    assert whatsapp.verify_signature(body, "sha256=" + _sign("s3cr3t", body)) is True


def test_verify_signature_invalid(monkeypatch):
    monkeypatch.setattr(config, "KAPSO_WEBHOOK_SECRET", "s3cr3t")
    assert whatsapp.verify_signature(b"payload", "deadbeef") is False


def test_verify_signature_no_secret(monkeypatch):
    monkeypatch.setattr(config, "KAPSO_WEBHOOK_SECRET", "")
    assert whatsapp.verify_signature(b"payload", "anything") is False
