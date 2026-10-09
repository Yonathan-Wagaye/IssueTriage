from fastapi import FastAPI, HTTPException, Request
from utils import parse_github_webhook, verify_github_webhook

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Triage App says hello!"}


@app.post("/webhooks/github")
async def webhook_github(request: Request):
    event = request.headers.get("X-GitHub-Event")
    github_secret = request.headers.get("X-Hub-Signature")
    raw_body = await request.body()
    if not verify_github_webhook(github_secret, raw_body):
        raise HTTPException(status_code=403, detail="Invalid webhook signature")

    print(f"GitHub event: {event}, body bytes: {len(raw_body)}")

    parsed_payload = parse_github_webhook(raw_body)
    print(f"Parsed payload: {parsed_payload}")
    return {"message": "Webhook received!"}
