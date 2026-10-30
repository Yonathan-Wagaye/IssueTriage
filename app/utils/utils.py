import hashlib
import hmac
import json
import os
import secrets
from datetime import UTC, datetime, timedelta

from app.models.models import (
    IssueInput,
    ParsedWebhook,
    RepositoryInput,
    TirageJobInput,
    WebhookDeliveryInput,
)

WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")
TIRAGE_JOB_LEASE_MINUTES = int(os.getenv("TIRAGE_JOB_LEASE_MINUTES", "10"))


def verify_github_webhook(github_secret: str | None, raw_body: bytes) -> bool:
    if not github_secret or not WEBHOOK_SECRET:
        return False

    expected = (
        "sha256="
        + hmac.new(WEBHOOK_SECRET.encode(), raw_body, hashlib.sha256).hexdigest()
    )

    return hmac.compare_digest(github_secret, expected)


SUPPORTED_ACTIONS = ("opened", "closed")


def parse_github_webhook(
    raw_body: bytes, event: str | None, delivery_id: str | None
) -> ParsedWebhook | None:
    if event != "issues" or not delivery_id:
        return None

    payload = json.loads(raw_body)
    action = payload["action"]
    if action not in SUPPORTED_ACTIONS:
        return None

    repo = payload["repository"]
    issue = payload["issue"]
    repository_id = str(repo["id"])

    return ParsedWebhook(
        repository=RepositoryInput(
            id=repository_id,
            name=repo["name"],
            url=repo["html_url"],
        ),
        webhook_delivery=WebhookDeliveryInput(
            github_delivery_id=delivery_id,
            repository_id=repository_id,
            event_type=event,
            action=action,
            received_at=datetime.now(UTC),
            github_created_at=issue["created_at"],
            github_updated_at=issue["updated_at"],
        ),
        issue=IssueInput(
            delivery_id=delivery_id,
            issue_number=issue["number"],
            title=issue["title"],
            body=issue["body"] or "",
            state=issue["state"],
        ),
    )


def generate_owner_token() -> str:
    return secrets.token_urlsafe(32)


def parse_issue_to_triage_job(issue: IssueInput) -> TirageJobInput:
    return TirageJobInput(
        issue_id=issue.id,
        status="pending",
        attempt_count=0,
        owner_token=generate_owner_token(),
        lease_expires_at=datetime.now(UTC)
        + timedelta(minutes=TIRAGE_JOB_LEASE_MINUTES),
        last_error=None,
        created_at=datetime.now(UTC),
    )
