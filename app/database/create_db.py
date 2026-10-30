import asyncio
from pathlib import Path

import aiosqlite

DB_PATH = Path(__file__).resolve().parent / "data" / "triageDB.db"

schema = """
CREATE TABLE IF NOT EXISTS repositories (
    id string PRIMARY KEY,
    name TEXT NOT NULL,
    url TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS webhook_deliveries (
    github_delivery_id string PRIMARY KEY,
    repository_id string NOT NULL,
    event_type TEXT NOT NULL CHECK(event_type='issues'),
    action TEXT NOT NULL CHECK (action='opened' OR action='closed'),
    received_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    github_created_at TEXT NOT NULL, 
    github_updated_at TEXT NOT NULL,

    CONSTRAINT fk_repository_id FOREIGN KEY (repository_id) REFERENCES repositories(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS issues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    delivery_id TEXT,
    issue_number INTEGER NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    state TEXT NOT NULL CHECK(state='open' OR state='closed'),

    CONSTRAINT fk_delivery_id FOREIGN KEY (delivery_id) REFERENCES webhook_deliveries(github_delivery_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS tirage_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    issue_id INTEGER NOT NULL,
    status TEXT NOT NULL CHECK(status='pending' OR status='running' OR status='completed' OR status='failed'),
    attempt_count INTEGER NOT NULL DEFAULT 0 CHECK(attempt_count <= 4),
    owner_token TEXT NOT NULL,
    lease_expires_at TEXT NOT NULL,
    last_error TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    CONSTRAINT fk_issue_id FOREIGN KEY (issue_id) REFERENCES issues(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS triage_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id integer NOT NULL,
    classification TEXT NOT NULL CHECK (classification='bug' OR classification='feature' OR classification='question' OR classification='documentation' OR classification='other'),
    priority TEXT NOT NULL CHECK (priority='low' OR priority='medium' OR priority='high'),
    summary TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    CONSTRAINT fk_job_id FOREIGN KEY (job_id) REFERENCES tirage_jobs(id) ON DELETE CASCADE
);
"""


async def create_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH, isolation_level=None) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        try:
            await db.executescript("BEGIN;\n" + schema)
            await db.commit()
        except Exception:
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(create_db())
