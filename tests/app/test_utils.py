import hashlib
import hmac

import pytest

from app.utils import utils
from app.utils.utils import parse_github_webhook, verify_github_webhook

TEST_SECRET = "test-webhook-secret"


def sign(body: bytes, secret: str = TEST_SECRET) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


@pytest.fixture
def webhook_secret(monkeypatch):
    monkeypatch.setattr(utils, "WEBHOOK_SECRET", TEST_SECRET)
    return TEST_SECRET


async def test_verify_github_webhook_valid_signature(webhook_secret, webhook_request):
    body = await webhook_request.body()

    assert verify_github_webhook(sign(body), body) is True


async def test_verify_github_webhook_wrong_secret(webhook_secret, webhook_request):
    body = await webhook_request.body()

    assert verify_github_webhook(sign(body, "wrong-secret"), body) is False


async def test_verify_github_webhook_tampered_body(webhook_secret, webhook_request):
    body = await webhook_request.body()

    assert verify_github_webhook(sign(body), body + b" ") is False


async def test_verify_github_webhook_missing_signature(webhook_secret, webhook_request):
    body = await webhook_request.body()

    assert verify_github_webhook(None, body) is False


async def test_verify_github_webhook_missing_server_secret(monkeypatch, webhook_request):
    monkeypatch.setattr(utils, "WEBHOOK_SECRET", None)
    body = await webhook_request.body()

    assert verify_github_webhook(sign(body), body) is False


async def test_parse_github_webhook(webhook_request, parsed_webhook_request):
    body = await webhook_request.body()
    result = parse_github_webhook(
        body,
        webhook_request.headers.get("X-GitHub-Event"),
        webhook_request.headers.get("X-GitHub-Delivery"),
    )

    # received_at is set to datetime.now() during parsing, so it can't match the fixture.
    exclude = {"webhook_delivery": {"received_at"}}
    assert result.model_dump(exclude=exclude) == parsed_webhook_request.model_dump(
        exclude=exclude
    )
