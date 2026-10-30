import aiosqlite

from app.database.create_db import DB_PATH
from app.models.models import (
    IssueInput,
    ParsedWebhook,
    RepositoryInput,
    TirageJobInput,
    WebhookDeliveryInput,
)
from app.utils.utils import parse_issue_to_triage_job


async def create_repository(
    db: aiosqlite.Connection, repository: RepositoryInput
) -> RepositoryInput:
    cursor = await db.execute(
        "SELECT 1 FROM repositories WHERE id = ?", (repository.id,)
    )
    if await cursor.fetchone() is not None:
        return repository

    await db.execute(
        "INSERT INTO repositories (id, name, url) VALUES (?, ?, ?)",
        (repository.id, repository.name, repository.url),
    )
    return repository


async def create_webhook_delivery(
    db: aiosqlite.Connection, webhook_delivery: WebhookDeliveryInput
) -> WebhookDeliveryInput:
    await db.execute(
        "INSERT INTO webhook_deliveries (github_delivery_id, repository_id, event_type, action, received_at, github_created_at, github_updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            webhook_delivery.github_delivery_id,
            webhook_delivery.repository_id,
            webhook_delivery.event_type,
            webhook_delivery.action,
            webhook_delivery.received_at,
            webhook_delivery.github_created_at,
            webhook_delivery.github_updated_at,
        ),
    )
    return webhook_delivery


async def create_issue(db: aiosqlite.Connection, issue: IssueInput) -> IssueInput:
    cursor = await db.execute(
        "INSERT INTO issues (delivery_id, issue_number, title, body, state) VALUES (?, ?, ?, ?, ?)",
        (issue.delivery_id, issue.issue_number, issue.title, issue.body, issue.state),
    )
    return issue.model_copy(update={"id": cursor.lastrowid})


async def create_triage_job(
    db: aiosqlite.Connection, triage_job: TirageJobInput
) -> TirageJobInput:
    cursor = await db.execute(
        "INSERT INTO tirage_jobs (issue_id, status, attempt_count, owner_token, lease_expires_at) VALUES (?, ?, ?, ?, ?)",
        (
            triage_job.issue_id,
            triage_job.status,
            triage_job.attempt_count,
            triage_job.owner_token,
            triage_job.lease_expires_at,
        ),
    )
    return triage_job.model_copy(update={"id": cursor.lastrowid})


async def queue_job_transaction(parsed: ParsedWebhook) -> TirageJobInput:
    async with aiosqlite.connect(DB_PATH, isolation_level=None) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        await db.execute("BEGIN")
        try:
            await create_repository(db, parsed.repository)
            await create_webhook_delivery(db, parsed.webhook_delivery)
            issue = await create_issue(db, parsed.issue)
            triage_job = await create_triage_job(db, parse_issue_to_triage_job(issue))
            await db.commit()
            return triage_job

        except Exception:
            await db.rollback()
            raise
