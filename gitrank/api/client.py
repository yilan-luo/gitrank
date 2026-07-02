"""GitHub API client with adaptive time slicing for date-range search.

Handles pagination, rate-limit tracking, and recursive time-window splitting
when the GitHub Search API returns more than 1000 total results.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta

import httpx

GITHUB_API_BASE = "https://api.github.com"
PER_PAGE = 100
MAX_RESULTS = 1000
MAX_DEPTH = 10


class GitHubClient:
    """Async GitHub API client for searching repositories.

    Uses the GitHub Search API with adaptive time slicing: when a query returns
    more than 1000 total results the date window is split in half and each half
    is fetched recursively, avoiding the 1000-result API cap.
    """

    def __init__(self, token: str | None = None) -> None:
        """Initialise the client.

        Args:
            token: Optional GitHub personal access token for higher rate limits.
        """
        self.token = token
        self.rate_limit_remaining: int | None = None
        self.rate_limit_reset: int | None = None
        self._http: httpx.AsyncClient | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def search_repos(
        self,
        topic: str,
        date_start: str,
        date_end: str,
        page: int = 1,
    ) -> dict:
        """Search repositories by topic and date range.

        Calls ``GET /search/repositories`` and returns the raw JSON response
        dict containing ``total_count``, ``incomplete_results``, and ``items``.

        Args:
            topic: GitHub topic tag (e.g. ``"machine-learning"``).
            date_start: ISO-format start date (``YYYY-MM-DD``).
            date_end: ISO-format end date (``YYYY-MM-DD``).
            page: Page number for pagination (1-based).

        Returns:
            The parsed JSON response dict.

        Raises:
            RuntimeError: If the API returns 403 (rate limit exceeded).
            httpx.HTTPStatusError: For other non-2xx responses.
        """
        if self._should_throttle():
            await asyncio.sleep(1)

        query = f"topic:{topic}+created:{date_start}..{date_end}"
        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": PER_PAGE,
            "page": page,
        }

        client = await self._get_client()
        response = await client.get("/search/repositories", params=params)
        self._update_rate_limit(response.headers)

        if response.status_code == 403:
            reset_ts = self.rate_limit_reset
            reset_info = (
                f" Resets at: {datetime.fromtimestamp(reset_ts)}"
                if reset_ts
                else ""
            )
            raise RuntimeError(
                f"GitHub API rate limit exceeded.{reset_info}"
            )

        response.raise_for_status()
        return response.json()

    async def adaptive_fetch(
        self,
        topic: str,
        date_start: str,
        date_end: str,
        depth: int = 0,
    ) -> list[dict]:
        """Fetch all repos for a time window, splitting recursively if needed.

        When ``total_count`` exceeds 1000 the time window is bisected and each
        half is fetched independently.  Results are deduplicated by ``id``.

        Splitting stops when:
        - ``total_count <= 1000``
        - the window is 1 day or less
        - ``depth`` reaches ``MAX_DEPTH`` (10)
        """
        result = await self.search_repos(topic, date_start, date_end, page=1)
        total_count: int = result["total_count"]

        date_start_dt = datetime.strptime(date_start, "%Y-%m-%d")
        date_end_dt = datetime.strptime(date_end, "%Y-%m-%d")
        window_days = (date_end_dt - date_start_dt).days

        # Decide whether to split the window
        if total_count > MAX_RESULTS and window_days > 1 and depth < MAX_DEPTH:
            # Bisect the date range
            mid = date_start_dt + (date_end_dt - date_start_dt) / 2
            mid_str = mid.strftime("%Y-%m-%d")
            next_day = (mid + timedelta(days=1)).strftime("%Y-%m-%d")

            left = await self.adaptive_fetch(
                topic, date_start, mid_str, depth + 1
            )
            right = await self.adaptive_fetch(
                topic, next_day, date_end, depth + 1
            )

            # Deduplicate by ``id`` (repos straddling the split boundary)
            seen: set[int] = set()
            merged: list[dict] = []
            for item in left + right:
                if item["id"] not in seen:
                    seen.add(item["id"])
                    merged.append(item)
            return merged

        # No splitting — paginate through all available results
        all_items: list[dict] = list(result.get("items", []))
        page = 2
        while len(all_items) < min(total_count, MAX_RESULTS):
            if self._should_throttle():
                await asyncio.sleep(1)
            page_result = await self.search_repos(
                topic, date_start, date_end, page=page
            )
            items: list[dict] = page_result.get("items", [])
            if not items:
                break
            all_items.extend(items)
            page += 1

        return all_items

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_headers(self) -> dict[str, str]:
        """Return HTTP headers including optional Authorization."""
        headers: dict[str, str] = {
            "Accept": "application/vnd.github.v3+json",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _update_rate_limit(self, headers: httpx.Headers) -> None:
        """Parse ``X-RateLimit-*`` headers from a response.

        Args:
            headers: The ``httpx.Response.headers`` object.
        """
        remaining = headers.get("X-RateLimit-Remaining")
        reset = headers.get("X-RateLimit-Reset")
        if remaining is not None:
            self.rate_limit_remaining = int(remaining)
        if reset is not None:
            self.rate_limit_reset = int(reset)

    async def _get_client(self) -> httpx.AsyncClient:
        """Return the shared ``httpx.AsyncClient``, creating it lazily.

        The client is reused across all ``search_repos`` calls so a single
        HTTP connection pool serves the entire lifetime of the
        ``GitHubClient`` instance.
        """
        if self._http is None:
            self._http = httpx.AsyncClient(
                base_url=GITHUB_API_BASE,
                headers=self._build_headers(),
            )
        return self._http

    async def close(self) -> None:
        """Close the underlying HTTP client and release connections."""
        if self._http is not None:
            await self._http.aclose()
            self._http = None

    def _should_throttle(self) -> bool:
        """Return ``True`` when the rate-limit is low and we should slow down.

        Returns ``False`` when ``rate_limit_remaining`` has not been set yet
        (i.e. before the first API call).
        """
        return (
            self.rate_limit_remaining is not None
            and self.rate_limit_remaining < 50
        )
