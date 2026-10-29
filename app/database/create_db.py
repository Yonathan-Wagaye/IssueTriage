import sqlite3

schema = """
CREATE TABLE IF NOT EXISTS repositories (
    id string PRIMARY KEY,
    name TEXT NOT NULL,
    url TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS webhook_deliveries (
    github_delivery_id string PRIMARY KEY,
    repository_id string NOT NULL,
    even_type TEXT NOT NULL CHECK(event_type='issues'),
    action TEXT NOT NULL CHECK (action='opened' OR action='closed'),
    received_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    github_created_at TEXT NOT NULL, 
    github_updated_at TEXT NOT NULL,

    CONSTRAINT fk_repository_id FOREIGN KEY (repository_id) REFERENCES repositories(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS issues (
    id interger PRIMARY KEY AUTOINCREMENT,
    delivery_id string NOT NULL,
    issue_number INTEGER NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    state TEXT NOT NULL CHECK(state='open' OR state='closed'),

    CONSTRAINT fk_delivery_id FOREIGN KEY (delivery_id) REFERENCES webhook_deliveries(github_delivery_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS tirage_jobs (
    id interger PRIMARY KEY AUTOINCREMENT,
    issue_id interger NOT NULL,
    status TEXT NOT NULL CHECK(status='pending' OR status='running' OR status='completed' OR status='failed'),
    attempt_count INTEGER NOT NULL DEFAULT 0 CHECK(attempt_count <= 4),
    onwer_token TEXT NOT NULL,
    lease_expires_at TEXT NOT NULL,
    last_error TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    CONSTRAINT fk_issue_id FOREIGN KEY (issue_id) REFERENCES issues(id) ON DELETE CASCADE,
    CONSTRAINT chk_lease_expires_at CHECK(lease_expires_at > strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE IF NOT EXISTS triage_results (
    id interger PRIMARY KEY AUTOINCREMENT,
    job_id integer NOT NULL,
    classification TEXT NOT NULL CHECK (classification='bug' OR classification='feature' OR classification='question' OR classification='documentation' OR classification='other'),
    priority TEXT NOT NULL CHECK (priority='low' OR priority='medium' OR priority='high'),
    summary TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    CONSTRAINT fk_job_id FOREIGN KEY (job_id) REFERENCES tirage_jobs(id) ON DELETE CASCADE
);
"""


def create_db():
    conn = sqlite3.connect("./data/triager.db")
    cursor = conn.cursor()
    cursor.executescript(schema)
    conn.commit()
    conn.close()


if __name__ == "__main__":
    create_db()
