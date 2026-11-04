"""
Asynchronous worker for the AI service.
"""

import asyncio

from openai import AsyncOpenAI
from openAI_service import summarize_issue
from repository.repository import validate_and_save_result

from database.connection import connect
from shared.schemas import IssueSummary


async def save_result(job_id: int, issue_summary: IssueSummary):
    async with connect() as db:
        await validate_and_save_result(db, job_id, issue_summary)


async def worker(worker_id: int, job_queue: asyncio.Queue, client: AsyncOpenAI):
    while True:
        job = await job_queue.get()

        try:
            result = await summarize_issue(client, job)
            await save_result(job.id, result)
            print(f"Worker {worker_id} evaluated job {job['id']} with result {result}")
        except Exception as e:
            print(
                f"Worker {worker_id} failed to evaluate job {job['id']} with error {e}"
            )
        finally:
            job_queue.task_done()
