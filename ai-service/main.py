import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from openai import AsyncOpenAI
from worker import worker

from shared.schemas import Job


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY")) as client:
        app.state.job_queue = asyncio.Queue(
            maxsize=int(os.getenv("MAX_JOB_QUEUE_SIZE"))
        )
        tasks = [
            worker(i, app.state.job_queue, client)
            for i in range(int(os.getenv("WORKERS_COUNT")))
        ]
        yield
        for task in tasks:
            task.cancel()

        await asyncio.gather(*tasks, return_exceptions=True)


app = FastAPI(lifespan=lifespan)


@app.get("/")
def read_root():
    return {"message": "AI Service says hello!"}


"""
class Job(BaseModel):
    id: int
    issue: IssueContent
    owner_token: str
    lease_expires_at: str
"""


@app.post("/summarize")
async def summarize_issue(job: Job, request: Request):
    try:
        await app.state.job_queue.put(job)
        return {"message": "Job queued"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
