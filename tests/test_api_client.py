"""Tests for gitrank.api.client — GitHubClient with respx mocking."""

from datetime import date, timedelta
from unittest.mock import AsyncMock

import httpx
import pytest
import respx

from gitrank.api.client import GitHubClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_item(github_id: int, full_name: str = "owner/repo") -> dict:
    """Build a minimal GitHub search API repo item dict."""
    return {
        "id": github_id,
        "full_name": full_name,
        "description": "A test repo",
        "language": "Python",
        "topics": ["test", "github"],
        "stargazers_count": 100,
        "forks_count": 10,
        "open_issues_count": 5,
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2025-06-01T08:00:00Z",
        "pushed_at": "2025-06-30T14:22:00Z",
        "html_url": f"https://github.com/{full_name}",
        "archived": False,
    }


# ---------------------------------------------------------------------------
# 1. search_repos() returns parsed results
# ---------------------------------------------------------------------------

@respx.mock
@pytest.mark.asyncio
async def test_search_repos_returns_parsed_results() -> None:
    """search_repos() returns a dict with total_count and items from the API."""
    respx.get("https://api.github.com/search/repositories").mock(
        return_value=httpx.Response(
            200,
            json={
                "total_count": 2,
                "incomplete_results": False,
                "items": [
                    _make_item(1, "a/b"),
                    _make_item(2, "c/d"),
                ],
            },
        )
    )

    client = GitHubClient()
    result = await client.search_repos("python", "2024-01-01", "2024-06-30")

    assert result["total_count"] == 2
    assert result["incomplete_results"] is False
    assert len(result["items"]) == 2
    assert result["items"][0]["id"] == 1
    assert result["items"][1]["full_name"] == "c/d"


# ---------------------------------------------------------------------------
# 2. search_repos() handles pagination
# ---------------------------------------------------------------------------

@respx.mock
@pytest.mark.asyncio
async def test_search_repos_handles_pagination() -> None:
    """search_repos() can fetch different pages with correct page parameter."""
    # Build mock items with page-dependent ids so we can distinguish
    def _build_response(request: httpx.Request) -> httpx.Response:
        page = int(request.url.params.get("page", "1"))
        start_id = (page - 1) * 100 + 1
        return httpx.Response(
            200,
            json={
                "total_count": 250,
                "incomplete_results": False,
                "items": [_make_item(i) for i in range(start_id, start_id + 100)],
            },
        )

    respx.get("https://api.github.com/search/repositories").mock(
        side_effect=_build_response
    )

    client = GitHubClient()

    page1 = await client.search_repos("rust", "2024-01-01", "2024-12-31", page=1)
    page2 = await client.search_repos("rust", "2024-01-01", "2024-12-31", page=2)

    assert len(page1["items"]) == 100
    assert len(page2["items"]) == 100
    # Different pages return different contiguous id ranges
    assert page1["items"][0]["id"] == 1
    assert page2["items"][0]["id"] == 101


# ---------------------------------------------------------------------------
# 3. search_repos() handles rate limit headers
# ---------------------------------------------------------------------------

@respx.mock
@pytest.mark.asyncio
async def test_search_repos_updates_rate_limit_headers() -> None:
    """search_repos() parses X-RateLimit-Remaining and X-RateLimit-Reset."""
    respx.get("https://api.github.com/search/repositories").mock(
        return_value=httpx.Response(
            200,
            json={"total_count": 1, "items": [_make_item(1)]},
            headers={
                "X-RateLimit-Remaining": "42",
                "X-RateLimit-Reset": "1700000000",
            },
        )
    )

    client = GitHubClient()
    await client.search_repos("go", "2024-01-01", "2024-06-30")

    assert client.rate_limit_remaining == 42
    assert client.rate_limit_reset == 1700000000


# ---------------------------------------------------------------------------
# 4. adaptive_fetch() paginates when total <= 1000
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_adaptive_fetch_returns_all_results_under_1000() -> None:
    """adaptive_fetch() paginates through all pages and returns every item."""
    client = GitHubClient()

    async def _mock_search(topic: str, date_start: str, date_end: str, page: int = 1) -> dict:
        per_page = 100
        total = 250
        start = (page - 1) * per_page + 1
        end = min(start + per_page - 1, total)
        items = [_make_item(i) for i in range(start, end + 1)]
        return {"total_count": total, "incomplete_results": False, "items": items}

    client.search_repos = AsyncMock(side_effect=_mock_search)  # type: ignore[method-assign]

    results = await client.adaptive_fetch("python", "2024-01-01", "2024-06-30")

    assert len(results) == 250
    assert results[0]["id"] == 1
    assert results[-1]["id"] == 250
    # Should have called search_repos for page 1, 2, 3
    assert client.search_repos.call_count == 3  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# 5. adaptive_fetch() triggers recursive time slicing when total > 1000
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_adaptive_fetch_splits_when_total_exceeds_1000() -> None:
    """adaptive_fetch() splits the time window and recurses when > 1000 results."""
    client = GitHubClient()

    async def _mock_search(topic: str, date_start: str, date_end: str, page: int = 1) -> dict:
        # Initial call: total > 1000 → triggers split
        if date_start == "2024-01-01" and date_end == "2024-06-30":
            return {
                "total_count": 2000,
                "incomplete_results": False,
                "items": [_make_item(i) for i in range(1, 101)],
            }
        # Left half (after split)
        if date_start == "2024-01-01":
            return {
                "total_count": 5,
                "incomplete_results": False,
                "items": [_make_item(i) for i in range(1, 6)],
            }
        # Right half (after split)
        return {
            "total_count": 5,
            "incomplete_results": False,
            "items": [_make_item(i) for i in range(100, 105)],
        }

    client.search_repos = AsyncMock(side_effect=_mock_search)  # type: ignore[method-assign]

    results = await client.adaptive_fetch("python", "2024-01-01", "2024-06-30")

    assert len(results) == 10
    # Deduplication should work — all 10 ids are unique
    ids = [r["id"] for r in results]
    assert len(ids) == len(set(ids))


# ---------------------------------------------------------------------------
# 6. adaptive_fetch() stops at max depth
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_adaptive_fetch_stops_at_max_depth() -> None:
    """adaptive_fetch() does not split further when depth reaches the maximum.

    Uses a wide date window so that *only* the depth guard stops the split.
    When splitting is stopped the function resorts to pagination (up to 1000).
    """
    client = GitHubClient()

    call_args: list[tuple] = []

    async def _mock_search(topic: str, date_start: str, date_end: str, page: int = 1) -> dict:
        call_args.append((topic, date_start, date_end, page))
        # Always return total > 1000 — would split if depth allowed it
        return {
            "total_count": 2000,
            "incomplete_results": False,
            "items": [_make_item(i) for i in range(1, 101)],
        }

    client.search_repos = AsyncMock(side_effect=_mock_search)  # type: ignore[method-assign]

    # Window = 9 days (> 1), so the only thing stopping a split is depth=10
    results = await client.adaptive_fetch("python", "2024-01-01", "2024-01-10", depth=10)

    # At max depth we don't split — fall through to pagination (up to 1000 items)
    assert len(results) == 1000
    # All calls used the original date range (no split ranges appeared)
    for _topic, ds, de, _page in call_args:
        assert ds == "2024-01-01"
        assert de == "2024-01-10"


# ---------------------------------------------------------------------------
# 7. _should_throttle() unit test
# ---------------------------------------------------------------------------

def test_should_throttle_returns_correctly() -> None:
    """_should_throttle() returns True only when remaining < 50."""
    client = GitHubClient()

    # rate_limit_remaining is None → don't throttle
    assert client._should_throttle() is False

    # Above 50 → don't throttle
    client.rate_limit_remaining = 100
    assert client._should_throttle() is False

    # Boundary: 50 → don't throttle
    client.rate_limit_remaining = 50
    assert client._should_throttle() is False

    # Below 50 → throttle
    client.rate_limit_remaining = 30
    assert client._should_throttle() is True
