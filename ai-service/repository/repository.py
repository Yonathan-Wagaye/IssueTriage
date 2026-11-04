import aiosqlite

from shared.schemas import IssueSummary


async def save_result(
    db: aiosqlite.Connection, job_id: int, issue_summary: IssueSummary
):
    cursor = await db.execute(
        "INSERT INTO triage_results (job_id, classification, priority, summary) VALUES (?, ?, ?, ?)",
        (job_id, issue_summary.category, issue_summary.priority, issue_summary.summary),
    )
    return cursor.lastrowid


async def validate_and_save_result(
    db: aiosqlite.Connection, owner_token: str, job_id: int, issue_summary: IssueSummary
) -> bool:
    try:
        await db.execute("BEGIN IMMEDIATE")

        cursor = await db.execute(
            "UPDATE triage_jobs SET status = 'completed' WHERE id = ? AND owner_token = ? AND status != 'completed' AND lease_expires_at > strftime('%Y-%m-%dT%H:%M:%fZ', 'now')",
            (job_id, owner_token),
        )
        if cursor.rowcount == 0:
            await db.rollback()
            return False
        await save_result(db, job_id, issue_summary)
        await db.commit()
        return True
    except Exception as e:
        await db.rollback()
        raise e
