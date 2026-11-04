import httpx
from fastapi import HTTPException
from schema import IssueInput, IssueSummary

from app.repositories.repository import queue_job_transaction, save_issue_summary

"""
Handles API calls to the AI service.

Components:
-> Single Transaction Save to DB (repository, webhook delivery, issue, triage job)
-> Call to AI serivce AI
"""


async def call_ai_service(
    issue: IssueInput, async_client: httpx.AsyncClient
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
        # save issue summary to DB
        await save_issue_summary(issue_summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI service error: {e}")
    return {"message": "Issue summarized successfully"}
