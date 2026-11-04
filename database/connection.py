from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import aiosqlite

from database.create_db import DB_PATH

BUSY_TIMEOUT_SECONDS = 5.0


@asynccontextmanager
async def connect() -> AsyncIterator[aiosqlite.Connection]:
    # isolation_level=None: no implicit transactions; callers run BEGIN/COMMIT themselves.
    # timeout: wait for the other service's write lock instead of failing with "database is locked".
    async with aiosqlite.connect(
        DB_PATH, isolation_level=None, timeout=BUSY_TIMEOUT_SECONDS
    ) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        yield db
