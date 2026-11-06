import sqlite3

import aiosqlite
import pytest

from app.repositories import repository
from app.repositories.repository import (
    create_issue,
    create_repository,
    create_webhook_delivery,
    queue_job_transaction,
    save_triage_result,
)
from shared.schemas import IssueSummary

TABLES = ("repositories", "webhook_deliveries", "issues", "triage_jobs")


async def count_rows(db, table: str) -> int:
    cursor = await db.execute(f"SELECT COUNT(*) FROM {table}")
    (count,) = await cursor.fetchone()
    return count


async def row_counts(db) -> dict[str, int]:
    return {table: await count_rows(db, table) for table in TABLES}


async def test_queue_job_transaction_commits_all_rows(
    db_connection, parsed_webhook_request
):
    job = await queue_job_transaction(parsed_webhook_request)

    assert job.id is not None
    assert job.status == "pending"
    assert await row_counts(db_connection) == {table: 1 for table in TABLES}

    cursor = await db_connection.execute(
        "SELECT i.issue_number, d.github_delivery_id, r.id "
        "FROM triage_jobs j "
        "JOIN issues i ON i.id = j.issue_id "
        "JOIN webhook_deliveries d ON d.github_delivery_id = i.delivery_id "
        "JOIN repositories r ON r.id = d.repository_id "
        "WHERE j.id = ?",
        (job.id,),
    )
    assert await cursor.fetchone() == (
        42,
        "7e1ef130-9e11-4a3b-bbb0-e5b244d0e831",
        "123456789",
    )


async def test_queue_job_transaction_rolls_back_on_failure(
    db_connection, parsed_webhook_request, monkeypatch
):
    async def failing_create_triage_job(db, triage_job):
        raise RuntimeError("Error creating triage job")

    monkeypatch.setattr(repository, "create_triage_job", failing_create_triage_job)

    with pytest.raises(RuntimeError, match="Error creating triage job"):
        await queue_job_transaction(parsed_webhook_request)

    # Repository, delivery and issue were inserted before the failure and must be undone.
    assert await row_counts(db_connection) == {table: 0 for table in TABLES}


async def test_queue_job_transaction_duplicate_delivery_is_rejected(
    db_connection, parsed_webhook_request
):
    await queue_job_transaction(parsed_webhook_request)

    with pytest.raises(sqlite3.IntegrityError):
        await queue_job_transaction(parsed_webhook_request)

    assert await row_counts(db_connection) == {table: 1 for table in TABLES}


async def test_queue_job_transaction_reuses_existing_repository(
    db_connection, parsed_webhook_request
):
    await queue_job_transaction(parsed_webhook_request)

    second_delivery_id = "second-delivery-id"
    second = parsed_webhook_request.model_copy(
        update={
            "webhook_delivery": parsed_webhook_request.webhook_delivery.model_copy(
                update={"github_delivery_id": second_delivery_id}
            ),
            "issue": parsed_webhook_request.issue.model_copy(
                update={"delivery_id": second_delivery_id, "issue_number": 43}
            ),
        }
    )
    await queue_job_transaction(second)

    assert await row_counts(db_connection) == {
        "repositories": 1,
        "webhook_deliveries": 2,
        "issues": 2,
        "triage_jobs": 2,
    }


async def test_queue_job_transaction_rolls_back_on_constraint_violation(
    db_connection, parsed_webhook_request
):
    # Passes model validation, but the delivery insert violates the CHECK on action
    # after the repository row has already been written.
    invalid = parsed_webhook_request.model_copy(
        update={
            "webhook_delivery": parsed_webhook_request.webhook_delivery.model_copy(
                update={"action": "edited"}
            )
        }
    )

    with pytest.raises(sqlite3.IntegrityError):
        await queue_job_transaction(invalid)

    assert await row_counts(db_connection) == {table: 0 for table in TABLES}


async def test_uncommitted_writes_are_not_visible_to_other_connections(
    db_file, db_connection, parsed_webhook_request
):
    async with aiosqlite.connect(db_file) as reader:
        await db_connection.execute("BEGIN")
        await create_repository(db_connection, parsed_webhook_request.repository)

        assert await count_rows(db_connection, "repositories") == 1
        assert await count_rows(reader, "repositories") == 0

        await db_connection.rollback()

        assert await count_rows(db_connection, "repositories") == 0
        assert await count_rows(reader, "repositories") == 0


async def test_foreign_keys_are_enforced(db_connection, parsed_webhook_request):
    with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"):
        await create_webhook_delivery(
            db_connection, parsed_webhook_request.webhook_delivery
        )

    with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"):
        await create_issue(db_connection, parsed_webhook_request.issue)


async def test_save_triage_result(db_connection, parsed_webhook_request):
    job = await queue_job_transaction(parsed_webhook_request)
    summary = IssueSummary(summary="Login is broken.", category="bug", priority="high")

    result_id = await save_triage_result(db_connection, job.id, summary)

    cursor = await db_connection.execute(
        "SELECT job_id, classification, priority, summary FROM triage_results WHERE id = ?",
        (result_id,),
    )
    assert await cursor.fetchone() == (job.id, "bug", "high", "Login is broken.")


async def test_save_triage_result_requires_existing_job(db_connection):
    summary = IssueSummary(summary="Orphan.", category="bug", priority="low")

    with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"):
        await save_triage_result(db_connection, 999, summary)
