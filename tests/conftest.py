"""
Pytest configuration file:
 -> Database (db file) fixture
 -> Database connection fixture
 -> Github issue webhook fixture
 -> Parsed Github issue webhook fixture
"""

import json
from datetime import UTC, datetime

import pytest
from fastapi import Request

from app.models.models import (
    IssueInput,
    ParsedWebhook,
    RepositoryInput,
    WebhookDeliveryInput,
)
from database import connection, create_db


@pytest.fixture
async def db_file(tmp_path, monkeypatch):
    path = tmp_path / "test.db"

    # connection.py imports DB_PATH by value, so both modules must be patched.
    monkeypatch.setattr(create_db, "DB_PATH", path)
    monkeypatch.setattr(connection, "DB_PATH", path)
    await create_db.create_db()
    return path


@pytest.fixture
async def db_connection(db_file):
    async with connection.connect() as conn:
        yield conn


@pytest.fixture
def webhook_request():
    payload = {
        "action": "opened",
        "issue": {
            "id": 987654321,
            "number": 42,
            "title": "Login fails",
            "body": "Login returns a server error.",
            "state": "open",
            "created_at": "2026-11-06T09:30:00Z",
            "updated_at": "2026-11-06T09:30:00Z",
        },
        "repository": {
            "id": 123456789,
            "name": "triage-app",
            "html_url": "https://github.com/yonathan/triage-app",
        },
    }

    # Convert the Python dictionary into JSON bytes.
    body = json.dumps(payload).encode("utf-8")

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/webhooks/github",
        "scheme": "http",
        "server": ("testserver", 80),
        "query_string": b"",
        "headers": [
            (b"content-type", b"application/json"),
            (b"x-github-event", b"issues"),
            (
                b"x-github-delivery",
                b"7e1ef130-9e11-4a3b-bbb0-e5b244d0e831",
            ),
        ],
    }

    sent = False

    async def receive():
        nonlocal sent

        if sent:
            return {"type": "http.disconnect"}

        sent = True
        return {
            "type": "http.request",
            "body": body,
            "more_body": False,
        }

    return Request(scope, receive)


@pytest.fixture
def parsed_webhook_request():
    return ParsedWebhook(
        repository=RepositoryInput(
            id="123456789",
            name="triage-app",
            url="https://github.com/yonathan/triage-app",
        ),
        webhook_delivery=WebhookDeliveryInput(
            github_delivery_id="7e1ef130-9e11-4a3b-bbb0-e5b244d0e831",
            repository_id="123456789",
            event_type="issues",
            action="opened",
            received_at=datetime(2026, 11, 6, 9, 30, tzinfo=UTC),
            github_created_at=datetime(2026, 11, 6, 9, 30, tzinfo=UTC),
            github_updated_at=datetime(2026, 11, 6, 9, 30, tzinfo=UTC),
        ),
        issue=IssueInput(
            delivery_id="7e1ef130-9e11-4a3b-bbb0-e5b244d0e831",
            issue_number=42,
            title="Login fails",
            body="Login returns a server error.",
            state="open",
        ),
    )
