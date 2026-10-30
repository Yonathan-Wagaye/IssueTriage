from datetime import UTC, datetime
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, PlainSerializer


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("datetime must include a timezone, e.g. a trailing 'Z'")
    return value.astimezone(UTC)


def _to_db_format(value: datetime) -> str:
    # Matches SQLite's strftime('%Y-%m-%dT%H:%M:%fZ'), which has millisecond precision.
    return value.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


UTCDateTime = Annotated[
    datetime,
    AfterValidator(_ensure_utc),
    PlainSerializer(_to_db_format, return_type=str),
]


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
