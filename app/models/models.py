from typing import Literal

from pydantic import BaseModel

from shared.schemas import UTCDateTime


class RepositoryInput(BaseModel):
    id: str
    name: str
    url: str


class WebhookDeliveryInput(BaseModel):
    github_delivery_id: str
    repository_id: str
    event_type: Literal["issues"]
    action: str
    received_at: UTCDateTime
    github_created_at: UTCDateTime
    github_updated_at: UTCDateTime


class IssueInput(BaseModel):
    id: int | None = None
    delivery_id: str
    issue_number: int
    title: str
    body: str
    state: Literal["open", "closed"]


class ParsedWebhook(BaseModel):
    repository: RepositoryInput
    webhook_delivery: WebhookDeliveryInput
    issue: IssueInput


class TirageJobInput(BaseModel):
    id: int | None = None
    issue_id: int
    status: str
    attempt_count: int
    owner_token: str
    lease_expires_at: UTCDateTime
    last_error: str | None = None
    created_at: UTCDateTime
