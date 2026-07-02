"""Pydantic data models for the GitHub Rank TUI application."""

from datetime import date, datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class Repository(BaseModel):
    """Represents a GitHub repository from the API response."""

    id: int
    full_name: str
    description: Optional[str] = None
    language: Optional[str] = None
    topics: List[str] = Field(default_factory=list)
    stargazers_count: int
    forks_count: int = Field(default=0)
    open_issues_count: int = Field(default=0)
    created_at: datetime
    updated_at: datetime
    pushed_at: datetime
    html_url: Optional[str] = None
    archived: bool = Field(default=False)


class StarSnapshot(BaseModel):
    """Records a star count at a point in time."""

    github_id: int
    stargazers_count: int
    recorded_at: datetime


class SearchParams(BaseModel):
    """Parameters collected during the wizard search."""

    topic: str
    date_start: date
    date_end: date
    sort: Literal["stars", "composite"] = "stars"
    limit: int = Field(default=20, ge=1, le=100)


class RankedRepo(BaseModel):
    """The ranked result shown in the results table."""

    rank: int
    repo: Repository
    stars_score: float = Field(ge=0, le=1)
    growth_score: float = Field(ge=0, le=1)
    activity_score: float = Field(ge=0, le=1)
    composite_score: float = Field(ge=0, le=1)
    growth_per_month: float
