"""Ranking engine for GitHub repositories.

Provides star-based and composite scoring with configurable weights:
  composite_score = 0.50 * S_star + 0.30 * S_growth + 0.20 * S_activity
"""

import math
from datetime import datetime, timezone
from typing import Dict, List, Optional

from ..api.models import RankedRepo, Repository


# ---------------------------------------------------------------------------
# Public ranking functions
# ---------------------------------------------------------------------------


def rank_by_stars(repos: List[Repository], limit: int = 20) -> List[RankedRepo]:
    """Rank repositories by star count descending.

    All score fields are populated, but ordering is purely by stargazers_count.
    Growth score uses the cold-start default (0.5) since no history is available.
    """
    if not repos:
        return []

    sorted_repos = sorted(repos, key=lambda r: r.stargazers_count, reverse=True)
    max_stars = max(r.stargazers_count for r in sorted_repos)

    results: List[RankedRepo] = []
    for i, repo in enumerate(sorted_repos[:limit]):
        stars_score = _calc_star_score(repo.stargazers_count, max_stars)
        growth_score = 0.5  # cold-start default
        activity_score = _calc_activity_score(repo, window_days=365)
        composite_score = (
            0.50 * stars_score + 0.30 * growth_score + 0.20 * activity_score
        )
        results.append(
            RankedRepo(
                rank=i + 1,
                repo=repo,
                stars_score=stars_score,
                growth_score=growth_score,
                activity_score=activity_score,
                composite_score=composite_score,
                growth_per_month=0.0,
            )
        )
    return results


def rank_by_composite(
    repos: List[Repository],
    window_days: int,
    star_history: Optional[Dict[int, List[int]]] = None,
    limit: int = 20,
) -> List[RankedRepo]:
    """Rank by composite score: 0.50*S_star + 0.30*S_growth + 0.20*S_activity.

    Args:
        repos: Repositories to rank.
        window_days: Activity window in days for _calc_activity_score.
        star_history: Optional mapping of repo id -> ordered list of star counts
            (assumed to be monthly snapshots; n entries = n-1 months of history).
        limit: Maximum number of results to return.
    """
    if not repos:
        return []

    max_stars = max(r.stargazers_count for r in repos)

    # Determine the maximum monthly growth across all repos with history
    max_growth = 0.0
    if star_history:
        for counts in star_history.values():
            if len(counts) >= 2:
                months = len(counts) - 1
                growth = (counts[-1] - counts[0]) / months
                if growth > max_growth:
                    max_growth = growth

    # Score every repo
    scored: List[tuple] = []
    for repo in repos:
        stars_score = _calc_star_score(repo.stargazers_count, max_stars)
        growth_score = _calc_growth_score(repo, max_growth, star_history)
        activity_score = _calc_activity_score(repo, window_days)
        composite_score = (
            0.50 * stars_score + 0.30 * growth_score + 0.20 * activity_score
        )

        # Per-repo growth_per_month for the output model
        growth_per_month = 0.0
        if star_history and repo.id in star_history:
            counts = star_history[repo.id]
            if len(counts) >= 2:
                months = len(counts) - 1
                growth_per_month = (counts[-1] - counts[0]) / months

        scored.append(
            (
                composite_score,
                stars_score,
                growth_score,
                activity_score,
                growth_per_month,
                repo,
            )
        )

    # Sort by composite_score descending
    scored.sort(key=lambda x: x[0], reverse=True)

    results: List[RankedRepo] = []
    for i, (composite, stars, growth, activity, gpm, repo) in enumerate(
        scored[:limit]
    ):
        results.append(
            RankedRepo(
                rank=i + 1,
                repo=repo,
                stars_score=stars,
                growth_score=growth,
                activity_score=activity,
                composite_score=composite,
                growth_per_month=gpm,
            )
        )
    return results


# ---------------------------------------------------------------------------
# Internal scoring helpers
# ---------------------------------------------------------------------------


def _calc_star_score(stars: int, max_stars: int) -> float:
    """log10 normalisation: log10(stars+1) / log10(max_stars+1).

    Returns 0.0 when *max_stars* is 0 (avoids division by zero).
    """
    if max_stars == 0:
        return 0.0
    return math.log10(stars + 1) / math.log10(max_stars + 1)


def _calc_growth_score(
    repo: Repository,
    max_growth: float,
    star_history: Optional[Dict[int, List[int]]] = None,
) -> float:
    """Calculate monthly growth score.

    * With *star_history*: extracts the historical star-count list for *repo*,
      computes ``new_stars_per_month``, then normalises via log10 against
      *max_growth*.
    * Without history (cold start): returns **0.5**.
    * When the repo is absent from *star_history* or has fewer than 2 data
      points: returns **0.5** (cold start).
    """
    if star_history is None or repo.id not in star_history:
        return 0.5

    counts = star_history[repo.id]
    if len(counts) < 2:
        return 0.5

    months = len(counts) - 1
    new_stars_per_month = (counts[-1] - counts[0]) / months

    if new_stars_per_month <= 0 or max_growth <= 0:
        return 0.0

    return math.log10(new_stars_per_month + 1) / math.log10(max_growth + 1)


def _calc_activity_score(repo: Repository, window_days: int) -> float:
    """Activity score based on recency of last push.

    ``1.0 - (days_since_pushed / window_days)``, clamped to **[0, 1]**.
    """
    now = datetime.now(timezone.utc)
    pushed = repo.pushed_at
    if pushed.tzinfo is None:
        # Defensively make naive datetimes UTC-aware
        pushed = pushed.replace(tzinfo=timezone.utc)

    days_since = (now - pushed).days
    score = 1.0 - (days_since / window_days)
    return max(0.0, min(1.0, score))
