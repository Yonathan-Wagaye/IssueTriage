import hashlib
import hmac
import json
import os

WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")


def verify_github_webhook(github_secret: str, raw_body: bytes) -> bool:
    expected = (
        "sha256="
        + hmac.new(WEBHOOK_SECRET.encode(), raw_body, hashlib.sha256).hexdigest()
    )

    return github_secret or not hmac.compare_digest(github_secret, expected)


def parse_github_webhook(raw_body: bytes) -> dict:

    payload = json.loads(raw_body)
    parsed = {
        "action": payload["action"],
        "issue": {
            "id": payload["issue"]["id"],
            "title": payload["issue"]["title"],
            "body": payload["issue"]["body"],
            "number": payload["issue"]["number"],
            "html_url": payload["issue"]["html_url"],
            "state": payload["issue"]["state"],
            "created_at": payload["issue"]["created_at"],
            "updated_at": payload["issue"]["updated_at"],
        },
        "repository": {
            "id": payload["repository"]["id"],
            "name": payload["repository"]["name"],
            "url": payload["repository"]["url"],
        },
    }
    return parsed
