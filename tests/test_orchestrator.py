"""Tests for gitrank.orchestrator -- QueryOrchestrator."""

from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gitrank.api.models import RankedRepo, Repository, SearchParams
from gitrank.cache.db import CacheDB
from gitrank.orchestrator import QueryOrchestrator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_repo_dict(github_id: int, full_name: str = "owner/repo") -> dict:
    """Build a minimal GitHub search API repo item dict."""
    return {
        "id": github_id,
        "full_name": full_name,
        "description": "A test repo",
        "language": "Python",
        "topics": ["test"],
        "stargazers_count": 100 * github_id,
        "forks_count": 10,
        "open_issues_count": 5,
        "created_at": "2024-03-15T10:30:00Z",
        "updated_at": "2025-06-01T08:00:00Z",
        "pushed_at": "2025-06-30T14:22:00Z",
        "html_url": f"https://github.com/{full_name}",
        "archived": False,
    }


def _make_params(**overrides) -> SearchParams:
    """Build SearchParams with sensible defaults."""
    defaults = {
        "topic": "python",
        "date_start": date(2024, 1, 1),
        "date_end": date(2024, 6, 30),
        "sort": "stars",
        "limit": 20,
    }
    defaults.update(overrides)
    return SearchParams(**defaults)


# ---------------------------------------------------------------------------
# 1. execute() returns cached results when cache hits
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_execute_returns_cached_results_when_cache_hits():
    """execute() loads from cache without calling the API when cache_hit is True."""
    cache = MagicMock(spec=CacheDB)
    cache.cache_hit.return_value = True

    now = datetime(2024, 3, 15, 10, 30, 0, tzinfo=timezone.utc)
    cached_repo = Repository(
        id=1,
        full_name="cached/repo",
        stargazers_count=500,
        created_at=now,
        updated_at=now,
        pushed_at=now,
    )
    cache.get_repositories_by_date.return_value = [cached_repo]

    client = MagicMock()
    client.adaptive_fetch = AsyncMock()

    orchestrator = QueryOrchestrator(cache=cache, client=client)
    params = _make_params()

    result = await orchestrator.execute(params)

    # Should NOT call the API
    client.adaptive_fetch.assert_not_called()
    # Should have called cache methods
    cache.cache_hit.assert_called_once()
    cache.get_repositories_by_date.assert_called_once()
    # Should return ranked results
    assert len(result) == 1
    assert isinstance(result[0], RankedRepo)
    assert result[0].repo.full_name == "cached/repo"
    assert result[0].rank == 1


# ---------------------------------------------------------------------------
# 2. execute() fetches from API when cache misses
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_execute_fetches_from_api_when_cache_misses():
    """execute() calls the API and caches results when cache_hit is False."""
    cache = MagicMock(spec=CacheDB)
    cache.cache_hit.return_value = False
    cache.get_repositories_by_date.return_value = []

    api_results = [
        _make_repo_dict(1, "api/repo1"),
        _make_repo_dict(2, "api/repo2"),
    ]

    client = MagicMock()
    client.adaptive_fetch = AsyncMock(return_value=api_results)

    orchestrator = QueryOrchestrator(cache=cache, client=client)
    params = _make_params()

    result = await orchestrator.execute(params)

    # Should call the API
    client.adaptive_fetch.assert_called_once()
    # Should upsert results into cache
    assert cache.upsert_repository.call_count == 2
    # Should return ranked results
    assert len(result) == 2
    assert isinstance(result[0], RankedRepo)
    assert result[0].repo.full_name == "api/repo2"  # higher stars → rank 1
    assert result[1].repo.full_name == "api/repo1"


# ---------------------------------------------------------------------------
# 3. execute() respects force_refresh=True
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_execute_respects_force_refresh():
    """execute() skips cache and hits the API when force_refresh=True,
    even when the cache would otherwise hit."""
    cache = MagicMock(spec=CacheDB)
    cache.cache_hit.return_value = True
    cache.get_repositories_by_date.return_value = []

    api_results = [_make_repo_dict(1, "fresh/repo")]

    client = MagicMock()
    client.adaptive_fetch = AsyncMock(return_value=api_results)

    orchestrator = QueryOrchestrator(cache=cache, client=client)
    params = _make_params()

    result = await orchestrator.execute(params, force_refresh=True)

    # Should skip cache and call API despite cache hit
    cache.cache_hit.assert_not_called()
    client.adaptive_fetch.assert_called_once()
    cache.upsert_repository.assert_called_once()

    assert len(result) == 1
    assert result[0].repo.full_name == "fresh/repo"


# ---------------------------------------------------------------------------
# 4. execute() ranks by stars sort
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_execute_ranks_by_stars_sort():
    """execute() with sort='stars' returns repos ordered by stars descending."""
    cache = MagicMock(spec=CacheDB)
    cache.cache_hit.return_value = False

    api_results = [
        _make_repo_dict(1, "low/repo"),     # 100 stars
        _make_repo_dict(3, "high/repo"),    # 300 stars
        _make_repo_dict(2, "mid/repo"),     # 200 stars
    ]

    client = MagicMock()
    client.adaptive_fetch = AsyncMock(return_value=api_results)

    orchestrator = QueryOrchestrator(cache=cache, client=client)
    params = _make_params(sort="stars", limit=3)

    result = await orchestrator.execute(params)

    assert len(result) == 3
    assert result[0].repo.full_name == "high/repo"
    assert result[0].rank == 1
    assert result[1].repo.full_name == "mid/repo"
    assert result[1].rank == 2
    assert result[2].repo.full_name == "low/repo"
    assert result[2].rank == 3


# ---------------------------------------------------------------------------
# 5. execute() ranks by composite sort
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_execute_ranks_by_composite_sort():
    """execute() with sort='composite' converts date range to window_days
    and routes to rank_by_composite, ordering by composite_score descending."""
    cache = MagicMock(spec=CacheDB)
    cache.cache_hit.return_value = False

    # Repos with different star counts, recency, etc. to produce distinct
    # composite scores
    api_results = [
        _make_repo_dict(1, "old/repo"),    # 100 stars, created long ago
        _make_repo_dict(10, "hot/repo"),   # 1000 stars, higher stars_score
        _make_repo_dict(5, "mid/repo"),    # 500 stars
    ]

    client = MagicMock()
    client.adaptive_fetch = AsyncMock(return_value=api_results)

    orchestrator = QueryOrchestrator(cache=cache, client=client)

    # date range = 2024-01-01 to 2024-12-31 → window_days = 365
    params = _make_params(
        sort="composite",
        date_start=date(2024, 1, 1),
        date_end=date(2024, 12, 31),
        limit=10,
    )

    result = await orchestrator.execute(params)

    # Should have called the API
    client.adaptive_fetch.assert_called_once()
    # Should return ranked results
    assert len(result) == 3
    assert all(isinstance(r, RankedRepo) for r in result)
    # Verify all composite scores are populated (not just stars)
    for r in result:
        assert 0.0 <= r.composite_score <= 1.0
        assert 0.0 <= r.stars_score <= 1.0
        assert 0.0 <= r.growth_score <= 1.0
        assert 0.0 <= r.activity_score <= 1.0
    # Ranks should be 1-based consecutive
    ranks = [r.rank for r in result]
    assert ranks == [1, 2, 3]
    # Sorted by composite_score descending
    scores = [r.composite_score for r in result]
    assert scores == sorted(scores, reverse=True)
