from dataclasses import dataclass
from typing import Optional

import httpx

from app.core.settings import settings


@dataclass(frozen=True)
class TelegramSendResult:
    ok: bool
    chat_id: Optional[str] = None
    message_id: Optional[str] = None
    error: Optional[str] = None


def _build_keyboard(public_key: str) -> dict:
    # callback_data formatı: "approve:<public_key>" / "reject:<public_key>"
    return {
        "inline_keyboard": [
            [
                {"text": "✅ Approve", "callback_data": f"approve:{public_key}"},
                {"text": "❌ Reject", "callback_data": f"reject:{public_key}"},
            ]
        ]
    }


def send_approval_message(*, public_key: str, text: str) -> TelegramSendResult:
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        return TelegramSendResult(ok=False, error="TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID missing")

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": settings.TELEGRAM_CHAT_ID,
        "text": text,
        "reply_markup": _build_keyboard(public_key),
        "disable_web_page_preview": True,
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.post(url, json=payload)
            data = r.json()
    except Exception as e:
        return TelegramSendResult(ok=False, error=str(e))

    if not data.get("ok"):
        return TelegramSendResult(ok=False, error=str(data))

    msg = data.get("result") or {}
    return TelegramSendResult(
        ok=True,
        chat_id=str(msg.get("chat", {}).get("id")),
        message_id=str(msg.get("message_id")),
        error=None,
    )

def edit_approval_message(chat_id: str, message_id: str, text: str) -> bool:
    if not settings.TELEGRAM_BOT_TOKEN:
        return False

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/editMessageText"
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "reply_markup": {"inline_keyboard": []}, # remove buttons
        "disable_web_page_preview": True,
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.post(url, json=payload)
            data = r.json()
            return data.get("ok", False)
    except Exception:
        return False