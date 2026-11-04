"""
Asynchronous worker for the AI service.
"""

import asyncio


async def evaluate_job(job: dict):
    """
    Evaluate the job and return the result.
    """
    await asyncio.sleep(1)
    return {"result": "success"}


async def worker(worker_id: int, job_queue: asyncio.Queue):
    while True:
        job = await job_queue.get()

        try:
            result = await evaluate_job(job)
            print(f"Worker {worker_id} evaluated job {job['id']} with result {result}")
        except Exception as e:
            print(
                f"Worker {worker_id} failed to evaluate job {job['id']} with error {e}"
            )
        finally:
            job_queue.task_done()
