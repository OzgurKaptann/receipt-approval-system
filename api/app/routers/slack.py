from __future__ import annotations

import hmac
import hashlib
import time
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.settings import settings
from app.services.workflow import on_slack_action

router = APIRouter(prefix="/slack", tags=["slack"])

logger = logging.getLogger(__name__)


async def verify_slack_signature(request: Request):
    if not settings.SLACK_SIGNING_SECRET:
        return  # Mock/Dev mode bypass if secret not provided

    slack_signature = request.headers.get("X-Slack-Signature")
    slack_request_timestamp = request.headers.get("X-Slack-Request-Timestamp")

    if not slack_signature or not slack_request_timestamp:
        raise HTTPException(status_code=401, detail="Missing Slack signature headers")

    if abs(time.time() - int(slack_request_timestamp)) > 60 * 5:
        raise HTTPException(status_code=401, detail="Replay attack detected")

    body = await request.body()
    sig_basestring = f"v0:{slack_request_timestamp}:{body.decode('utf-8')}"

    my_signature = "v0=" + hmac.new(
        settings.SLACK_SIGNING_SECRET.encode(),
        sig_basestring.encode(),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(my_signature, slack_signature):
        raise HTTPException(status_code=401, detail="Invalid Slack signature")


@router.post("/webhook", dependencies=[Depends(verify_slack_signature)])
async def slack_webhook(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    payload_str = form.get("payload")

    if not payload_str:
        logger.error("Missing payload in Slack webhook form data")
        raise HTTPException(status_code=400, detail="Missing payload")

    try:
        data = json.loads(payload_str)
    except json.JSONDecodeError:
        logger.error("Failed to decode Slack payload JSON")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    if data.get("type") != "block_actions":
        return {"ok": True}

    actions = data.get("actions", [])
    if not actions:
        return {"ok": True}

    action_val = actions[0].get("value", "")
    try:
        action_type, public_key = action_val.split(":", 1)
    except ValueError:
        logger.error(f"Invalid action value format: {action_val}")
        return {"ok": True}

    if action_type not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="Invalid action")

    actor = data.get("user", {})
    logger.info(
        f"Slack Webhook Hit: Action={action_type}, PublicKey={public_key}, User={actor.get('username')}"
    )

    try:
        doc, dep = on_slack_action(
            db,
            public_key=public_key,
            action=action_type,
            actor=actor,
        )
    except ValueError as exc:
        logger.error(f"Error executing slack action: {exc}")
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    response_url = data.get("response_url")
    if response_url:
        import httpx

        display_name = actor.get("username") or actor.get("id") or "unknown"

        if action_type == "approve":
            new_text = f"✅ Receipt approved by {display_name} (`{public_key}`)"
        else:
            new_text = f"❌ Receipt rejected by {display_name} (`{public_key}`)"

        update_payload = {
            "replace_original": True,
            "text": new_text,
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": new_text
                    }
                }
            ]
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                r = client.post(response_url, json=update_payload)
                logger.info(f"Slack message updated to {action_type.upper()} for {public_key}: HTTP {r.status_code}")
        except Exception as e:
            logger.error(f"Failed to update Slack message for {public_key} via response_url: {e}")

    return {
        "ok": True,
        "status": doc.status,
        "public_key": public_key,
        "deposit_id": str(getattr(dep, "id", "")) if getattr(dep, "id", None) else None,
    }