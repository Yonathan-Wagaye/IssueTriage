from datetime import UTC, datetime
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, PlainSerializer, TypeAdapter


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("datetime must include a timezone, e.g. a trailing 'Z'")
    return value.astimezone(UTC)


def to_db_timestamp(value: datetime) -> str:
    # Matches SQLite's strftime('%Y-%m-%dT%H:%M:%fZ'), which has millisecond precision.
    return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


UTCDateTime = Annotated[
    datetime,
    AfterValidator(_ensure_utc),
    PlainSerializer(to_db_timestamp, return_type=str),
]

_utc_datetime_adapter = TypeAdapter(UTCDateTime)


def from_db_timestamp(value: str) -> datetime:
    return _utc_datetime_adapter.validate_python(value)


class IssueContent(BaseModel):
    title: str
    body: str


class IssueSummary(BaseModel):
    summary: str
    category: Literal["bug", "feature", "question", "documentation", "other"]
    priority: Literal["low", "medium", "high"]


class Job(BaseModel):
    id: int
    issue: IssueContent
    owner_token: str
    lease_expires_at: UTCDateTime
