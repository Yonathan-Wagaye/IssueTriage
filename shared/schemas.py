from typing import Literal

from pydantic import BaseModel


class IssueContent(BaseModel):
    title: str
    body: str


class IssueSummary(BaseModel):
    summary: str
    category: Literal["bug", "feature", "question", "documentation", "other"]
    priority: Literal["low", "medium", "high"]


class Job(BaseModel):
    id: int
    issue: IssueContent
    owner_token: str
    lease_expires_at: str
