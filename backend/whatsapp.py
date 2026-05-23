"""Thin Kapso WhatsApp client.

Kapso exposes a REST API that mirrors Meta's WhatsApp Cloud API. Keeping all
provider-specific details here means swapping to Twilio/Meta later touches only
this file.
"""
import hashlib
import hmac
from typing import List

import requests

from . import config


def _endpoint() -> str:
    return f"{config.KAPSO_API_BASE}/{config.KAPSO_PHONE_NUMBER_ID}/messages"


def _headers() -> dict:
    return {
        "Content-Type": "application/json",
        "X-API-Key": config.KAPSO_API_KEY,
    }


def _post(payload: dict) -> requests.Response:
    response = requests.post(
        _endpoint(), headers=_headers(), json=payload, timeout=15
    )
    if not response.ok:
        # Surface the provider error so callers/logs can see what failed.
        raise RuntimeError(
            f"Kapso send failed: {response.status_code} - {response.text}"
        )
    return response


def send_text(to: str, body: str) -> requests.Response:
    """Free-form text. Only allowed within 24h of the user's last message."""
    return _post(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"body": body},
        }
    )


def send_template(
    to: str,
    template_name: str,
    body_params: List[str],
    lang: str = "es",
) -> requests.Response:
    """Approved template message, required for proactive (outside-24h) sends."""
    components = []
    if body_params:
        components.append(
            {
                "type": "body",
                "parameters": [{"type": "text", "text": p} for p in body_params],
            }
        )
    return _post(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": lang},
                "components": components,
            },
        }
    )


def verify_signature(raw_body: bytes, signature_header: str) -> bool:
    """Constant-time check of the X-Webhook-Signature HMAC-SHA256 header."""
    if not config.KAPSO_WEBHOOK_SECRET or not signature_header:
        return False
    expected = hmac.new(
        config.KAPSO_WEBHOOK_SECRET.encode(), raw_body, hashlib.sha256
    ).hexdigest()
    # Tolerate an optional "sha256=" prefix some providers add.
    provided = signature_header.split("=", 1)[-1].strip()
    return hmac.compare_digest(expected, provided)
