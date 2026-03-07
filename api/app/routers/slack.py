from __future__ import annotations

import hmac
import hashlib
import time

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.settings import settings
from app.schemas.slack import SlackWebhookRequest, SlackWebhookResponse
from app.services.workflow import on_slack_action


router = APIRouter(prefix="/slack", tags=["slack"])


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

@router.post("/webhook", response_model=SlackWebhookResponse, dependencies=[Depends(verify_slack_signature)])
def slack_webhook(payload: SlackWebhookRequest, db: Session = Depends(get_db)) -> SlackWebhookResponse:
    action = payload.action.lower().strip()
    if action not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="Invalid action")

    try:
        doc, dep = on_slack_action(
            db,
            public_key=payload.public_key,
            action=action,  # type: ignore[arg-type]
            actor=payload.actor.model_dump(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return SlackWebhookResponse(
        ok=True,
        status=doc.status,
        public_key=payload.public_key,
        deposit_id=getattr(dep, "id", None) if dep is not None else None,
    )

