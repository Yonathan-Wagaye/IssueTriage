import httpx
from fastapi import HTTPException

from app.models.models import ParsedWebhook
from app.repositories.repository import queue_job_transaction, save_triage_result
from shared.schemas import IssueSummary

"""
Handles API calls to the AI service.

Components:
-> Single Transaction Save to DB (repository, webhook delivery, issue, triage job)
-> Call to AI serivce AI
"""


async def call_ai_service(
    issue: ParsedWebhook, async_client: httpx.AsyncClient
) -> IssueSummary:
    try:
        # single transaction save to DB
        await queue_job_transaction(issue)
        # call AI service
        response = await async_client.post(
            "http://localhost:8000/openai/summarize",
            json=issue.model_dump(),
        )
        issue_summary = IssueSummary.model_validate_json(response.json())
        # save triage result to DB
        await save_triage_result(issue_summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI service error: {e}")
    return {"message": "Issue summarized successfully"}
