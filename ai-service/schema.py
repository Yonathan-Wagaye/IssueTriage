from typing import Literal

from pydantic import BaseModel


class IssueInput(BaseModel):
    title: str
    body: str


class IssueSummary(BaseModel):
    summary: str
    category: Literal["bug", "feature", "question", "documentation", "other"]
    priority: Literal["low", "medium", "high"]
