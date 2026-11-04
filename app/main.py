import os
from contextlib import asynccontextmanager

import httpx
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request

from app.external.ai_service import call_ai_service
from app.utils.utils import parse_github_webhook, verify_github_webhook


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.ai_service_client = httpx.AsyncClient()
    app.state.ai_service_client.base_url = os.getenv("AI_SERVICE_URL")
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
def read_root():
    return {"message": "Triage App says hello!"}


@app.post("/webhooks/github")
async def webhook_github(request: Request, background_tasks: BackgroundTasks):
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

    # background task to call AI service
    background_tasks.add_task(
        call_ai_service, parsed_payload, app.state.ai_service_client
    )

    return {"message": "Webhook received and being processed!"}
