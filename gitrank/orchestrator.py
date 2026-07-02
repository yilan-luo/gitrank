"""Query orchestrator that wires cache, API, and ranking together.

``QueryOrchestrator.execute`` is the main entry point: it checks the cache
first, falls back to the GitHub API on a miss, persists fetched results,
and finally ranks them using the configured sort strategy.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from gitrank.api.client import GitHubClient
from gitrank.api.models import RankedRepo, Repository, SearchParams
from gitrank.cache.db import CacheDB
from gitrank.rank.engine import rank_by_composite, rank_by_stars


class QueryOrchestrator:
    """Coordinates a full search-and-rank pipeline.

    Typical usage::

        orchestrator = QueryOrchestrator(cache=CacheDB(), client=GitHubClient())
        params = SearchParams(topic="ai", date_start=..., date_end=...)
        results = await orchestrator.execute(params)
    """

    def __init__(self, cache: CacheDB, client: GitHubClient) -> None:
        """Initialise the orchestrator.

        Args:
            cache: An initialised ``CacheDB`` instance.
            client: A ``GitHubClient`` instance.
        """
        self.cache = cache
        self.client = client

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def execute(
        self,
        params: SearchParams,
        force_refresh: bool = False,
    ) -> List[RankedRepo]:
        """Execute a search query: cache-first, fallback to API, then rank.

        Args:
            params: Search parameters (topic, date range, sort, limit).
            force_refresh: When ``True`` the cache is bypassed entirely.

        Returns:
            A list of ``RankedRepo`` ordered by the chosen sort strategy.
        """
        repos: List[Repository] = []

        if not force_refresh and self.cache.cache_hit(
            topic=params.topic,
            date_start=params.date_start,
            date_end=params.date_end,
        ):
            # Cache hit — load repos directly from SQLite
            repos = self.cache.get_repositories_by_date(
                date_start=params.date_start,
                date_end=params.date_end,
                topic=params.topic,
            )
        else:
            # Cache miss (or forced refresh) — hit the GitHub API
            date_start_str = params.date_start.isoformat()
            date_end_str = params.date_end.isoformat()
            raw_items = await self.client.adaptive_fetch(
                topic=params.topic,
                date_start=date_start_str,
                date_end=date_end_str,
            )
            repos = self._to_repository_models(raw_items)

            # Persist every fetched repo into the cache
            for repo in repos:
                self.cache.upsert_repository(repo)

        # Rank using the requested strategy
        if params.sort == "composite":
            window_days = (params.date_end - params.date_start).days or 365
            return rank_by_composite(repos, window_days=window_days, limit=params.limit)
        else:
            return rank_by_stars(repos, limit=params.limit)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _to_repository_models(self, repo_dicts: List[dict]) -> List[Repository]:
        """Convert raw GitHub API dicts into ``Repository`` Pydantic models.

        Dates are parsed from ISO-format strings.  Any dict that fails
        validation is silently skipped so a single malformed item does not
        break the entire pipeline.

        Args:
            repo_dicts: Raw ``items`` entries from the GitHub Search API.

        Returns:
            A list of validated ``Repository`` instances.
        """
        models: List[Repository] = []
        for item in repo_dicts:
            try:
                models.append(
                    Repository(
                        id=item["id"],
                        full_name=item.get("full_name", ""),
                        description=item.get("description"),
                        language=item.get("language"),
                        topics=item.get("topics", []),
                        stargazers_count=item.get("stargazers_count", 0),
                        forks_count=item.get("forks_count", 0),
                        open_issues_count=item.get("open_issues_count", 0),
                        created_at=_parse_dt(item.get("created_at")),
                        updated_at=_parse_dt(item.get("updated_at")),
                        pushed_at=_parse_dt(item.get("pushed_at")),
                        html_url=item.get("html_url"),
                        archived=item.get("archived", False),
                    )
                )
            except Exception:
                # Skip items that fail validation (e.g. missing required fields)
                continue
        return models


# ------------------------------------------------------------------
# Module-level helpers
# ------------------------------------------------------------------


def _parse_dt(value: Optional[str]) -> datetime:
    """Parse an ISO-format datetime string, falling back to epoch on failure.

    Args:
        value: ISO-8601 string (e.g. ``"2024-03-15T10:30:00Z"``) or ``None``.

    Returns:
        A timezone-aware ``datetime``.
    """
    if value is None:
        return datetime(1970, 1, 1, tzinfo=timezone.utc)
    try:
        # Handle 'Z' suffix manually for broader Python version compatibility
        normalized = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return datetime(1970, 1, 1, tzinfo=timezone.utc)
