from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request

from app.repositories.repository import queue_job_transaction
from app.utils.utils import parse_github_webhook, verify_github_webhook


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
def read_root():
    return {"message": "Triage App says hello!"}


@app.post("/webhooks/github")
async def webhook_github(request: Request):
    event = request.headers.get("X-GitHub-Event")
    github_secret = request.headers.get("X-Hub-Signature-256")
    raw_body = await request.body()
    if not verify_github_webhook(github_secret, raw_body):
        raise HTTPException(status_code=403, detail="Invalid webhook signature")

    print(f"GitHub event: {event}, body bytes: {len(raw_body)}")

    parsed_payload = parse_github_webhook(
        raw_body, event, request.headers.get("X-GitHub-Delivery")
    )
    if parsed_payload is None:
        return {"message": "Webhook ignored"}

    triage_job = await queue_job_transaction(parsed_payload)

    # Call the AI service to summarize the issue

    print(f"Queued triage job {triage_job.id} for issue {triage_job.issue_id}")
    return {"message": "Webhook received!", "triage_job_id": triage_job.id}
