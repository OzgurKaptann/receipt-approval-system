from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.slack import SlackWebhookRequest, SlackWebhookResponse
from app.services.workflow import on_slack_action


router = APIRouter(prefix="/slack", tags=["slack"])


@router.post("/webhook", response_model=SlackWebhookResponse)
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

