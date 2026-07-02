"""Tests for gitrank.api.models — Pydantic data models."""

from datetime import date, datetime, timezone

import pytest
from pydantic import ValidationError


# ---------------------------------------------------------------------------
# Repository
# ---------------------------------------------------------------------------

def test_repository_from_full_dict() -> None:
    """Parse a Repository from a dict with all fields present."""
    from gitrank.api.models import Repository

    data = {
        "id": 12345,
        "full_name": "owner/repo",
        "description": "A test repository",
        "language": "Python",
        "topics": ["cli", "tui", "github"],
        "stargazers_count": 1500,
        "forks_count": 300,
        "open_issues_count": 12,
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2025-06-01T08:00:00Z",
        "pushed_at": "2025-06-30T14:22:00Z",
        "html_url": "https://github.com/owner/repo",
        "archived": False,
    }
    repo = Repository(**data)

    assert repo.id == 12345
    assert repo.full_name == "owner/repo"
    assert repo.description == "A test repository"
    assert repo.language == "Python"
    assert repo.topics == ["cli", "tui", "github"]
    assert repo.stargazers_count == 1500
    assert repo.forks_count == 300
    assert repo.open_issues_count == 12
    assert isinstance(repo.created_at, datetime)
    assert isinstance(repo.updated_at, datetime)
    assert isinstance(repo.pushed_at, datetime)
    assert repo.html_url == "https://github.com/owner/repo"
    assert repo.archived is False


def test_repository_minimal_fields_defaults() -> None:
    """Repository with only required fields: defaults are applied for the rest."""
    from gitrank.api.models import Repository

    data = {
        "id": 999,
        "full_name": "minimal/repo",
        "description": None,
        "language": None,
        "stargazers_count": 42,
        "created_at": "2024-03-01T00:00:00Z",
        "updated_at": "2024-03-10T00:00:00Z",
        "pushed_at": "2024-03-05T00:00:00Z",
    }
    repo = Repository(**data)

    # Required fields
    assert repo.id == 999
    assert repo.full_name == "minimal/repo"
    assert repo.stargazers_count == 42

    # Defaults
    assert repo.topics == []
    assert repo.forks_count == 0
    assert repo.open_issues_count == 0
    assert repo.html_url is None
    assert repo.archived is False
    assert repo.description is None
    assert repo.language is None


# ---------------------------------------------------------------------------
# StarSnapshot
# ---------------------------------------------------------------------------

def test_starsnapshot_parsing() -> None:
    """StarSnapshot parsing from dict with all fields."""
    from gitrank.api.models import StarSnapshot

    now = datetime.now(timezone.utc)
    data = {
        "github_id": 555,
        "stargazers_count": 1200,
        "recorded_at": now.isoformat(),
    }
    snap = StarSnapshot(**data)

    assert snap.github_id == 555
    assert snap.stargazers_count == 1200
    assert isinstance(snap.recorded_at, datetime)


# ---------------------------------------------------------------------------
# SearchParams
# ---------------------------------------------------------------------------

def test_searchparams_valid_defaults() -> None:
    """SearchParams with required fields only — defaults kick in."""
    from gitrank.api.models import SearchParams

    params = SearchParams(
        topic="machine-learning",
        date_start=date(2024, 1, 1),
        date_end=date(2024, 6, 30),
    )

    assert params.topic == "machine-learning"
    assert params.date_start == date(2024, 1, 1)
    assert params.date_end == date(2024, 6, 30)
    assert params.sort == "stars"        # default
    assert params.limit == 20             # default


def test_searchparams_limit_validation() -> None:
    """SearchParams.limit must be between 1 and 100 (inclusive)."""
    from gitrank.api.models import SearchParams

    # Below minimum (0) — should raise
    with pytest.raises(ValidationError):
        SearchParams(
            topic="rust",
            date_start=date(2024, 1, 1),
            date_end=date(2024, 12, 31),
            limit=0,
        )

    # Above maximum (101) — should raise
    with pytest.raises(ValidationError):
        SearchParams(
            topic="rust",
            date_start=date(2024, 1, 1),
            date_end=date(2024, 12, 31),
            limit=101,
        )

    # Edge values should pass
    params_min = SearchParams(
        topic="go",
        date_start=date(2024, 1, 1),
        date_end=date(2024, 6, 30),
        limit=1,
    )
    assert params_min.limit == 1

    params_max = SearchParams(
        topic="go",
        date_start=date(2024, 1, 1),
        date_end=date(2024, 6, 30),
        limit=100,
    )
    assert params_max.limit == 100


# ---------------------------------------------------------------------------
# RankedRepo
# ---------------------------------------------------------------------------

def test_rankedrepo_creation() -> None:
    """RankedRepo can be created with valid Repository and score data."""
    from gitrank.api.models import RankedRepo, Repository

    repo = Repository(
        id=1,
        full_name="trending/repo",
        description="A trending repo",
        language="Rust",
        stargazers_count=5000,
        created_at="2024-01-01T00:00:00Z",
        updated_at="2025-07-01T00:00:00Z",
        pushed_at="2025-06-28T00:00:00Z",
    )

    ranked = RankedRepo(
        rank=1,
        repo=repo,
        stars_score=0.95,
        growth_score=0.78,
        activity_score=0.82,
        composite_score=0.85,
        growth_per_month=125.5,
    )

    assert ranked.rank == 1
    assert ranked.repo is repo
    assert ranked.stars_score == 0.95
    assert ranked.growth_score == 0.78
    assert ranked.activity_score == 0.82
    assert ranked.composite_score == 0.85
    assert ranked.growth_per_month == 125.5
