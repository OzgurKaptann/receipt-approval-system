from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

import httpx

from app.core.settings import settings


SLACK_API_URL = "https://slack.com/api/chat.postMessage"


@dataclass(frozen=True)
class SlackSendResult:
    ok: bool
    channel_id: Optional[str] = None
    message_ts: Optional[str] = None
    error: Optional[str] = None
    is_mock: bool = False


def _format_slack_text(
    *,
    public_key: str,
    sender_name: Optional[str],
    amount_try: Optional[Decimal],
    transfer_date: Optional[datetime],
) -> str:
    lines = ["🧾 *Receipt Approval (Slack)*"]
    lines.append(f"- public_key: `{public_key}`")
    if sender_name:
        lines.append(f"- sender: {sender_name}")
    if amount_try is not None:
        lines.append(f"- amount_try: {amount_try}")
    if transfer_date is not None:
        lines.append(f"- transfer_date: {transfer_date.isoformat()}")
    return "\n".join(lines)


def send_approval_request(
    *,
    public_key: str,
    sender_name: Optional[str],
    amount_try: Optional[Decimal],
    transfer_date: Optional[datetime],
) -> tuple[str, str]:
    """
    Sends a Slack approval request or returns mock ids when Slack is not configured.

    Returns:
        (channel_id, message_ts)
    """
    text = _format_slack_text(
        public_key=public_key,
        sender_name=sender_name,
        amount_try=amount_try,
        transfer_date=transfer_date,
    )

    token = settings.SLACK_BOT_TOKEN
    channel = settings.SLACK_CHANNEL_ID

    if not token or not channel:
        # Mock mode: behave as if Slack accepted the message.
        return "mock_channel", "mock_ts"

    import logging
    logger = logging.getLogger(__name__)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8",
    }
    
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": text,
            }
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Approve"},
                    "style": "primary",
                    "value": f"approve:{public_key}",
                    "action_id": "approve_action"
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Reject"},
                    "style": "danger",
                    "value": f"reject:{public_key}",
                    "action_id": "reject_action"
                }
            ]
        }
    ]

    payload = {
        "channel": channel,
        "text": text,
        "blocks": blocks,
    }

    with httpx.Client(timeout=10.0) as client:
        resp = client.post(SLACK_API_URL, json=payload, headers=headers)
        data = resp.json()

    if not data.get("ok"):
        logger.error(f"Slack API error (HTTP {resp.status_code}): {data}")
        raise RuntimeError(f"Slack API error: {data!r}")
    else:
        logger.info(f"Successfully dispatched Slack message to channel {channel} for document {public_key}")

    channel_id = str(data.get("channel"))
    message_ts = str(data.get("ts"))
    return channel_id, message_ts

