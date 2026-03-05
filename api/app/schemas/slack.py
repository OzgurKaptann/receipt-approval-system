from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SlackActor(BaseModel):
    username: Optional[str] = None
    id: Optional[str] = Field(default=None, description="Slack user id")


class SlackWebhookRequest(BaseModel):
    action: str
    public_key: str
    actor: SlackActor


class SlackWebhookResponse(BaseModel):
    ok: bool
    status: str
    public_key: str
    deposit_id: Optional[UUID] = None

