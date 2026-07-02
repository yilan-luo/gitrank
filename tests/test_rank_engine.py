"""Tests for gitrank.rank.engine -- ranking engine."""

from datetime import datetime, timedelta, timezone
from typing import Optional

import pytest

from gitrank.api.models import Repository, RankedRepo


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_repo(
    github_id: int = 1,
    full_name: str = "owner/repo",
    stargazers_count: int = 100,
    pushed_at: Optional[datetime] = None,
) -> Repository:
    """Build a Repository model with sensible defaults for ranking tests."""
    now = datetime(2025, 7, 1, 12, 0, 0, tzinfo=timezone.utc)
    return Repository(
        id=github_id,
        full_name=full_name,
        stargazers_count=stargazers_count,
        created_at=now,
        updated_at=now,
        pushed_at=pushed_at if pushed_at is not None else now,
    )


# ---------------------------------------------------------------------------
# rank_by_stars
# ---------------------------------------------------------------------------


def test_rank_by_stars_empty_list() -> None:
    """rank_by_stars returns empty list for empty input."""
    from gitrank.rank.engine import rank_by_stars

    result = rank_by_stars([])
    assert result == []


def test_rank_by_stars_sorts_by_stars_descending() -> None:
    """rank_by_stars sorts repos by stargazers_count descending."""
    from gitrank.rank.engine import rank_by_stars

    repos = [
        _make_repo(github_id=1, full_name="low/repo", stargazers_count=10),
        _make_repo(github_id=2, full_name="high/repo", stargazers_count=1000),
        _make_repo(github_id=3, full_name="mid/repo", stargazers_count=500),
    ]

    result = rank_by_stars(repos)

    assert len(result) == 3
    assert result[0].repo.full_name == "high/repo"
    assert result[0].rank == 1
    assert result[1].repo.full_name == "mid/repo"
    assert result[1].rank == 2
    assert result[2].repo.full_name == "low/repo"
    assert result[2].rank == 3


def test_rank_by_stars_respects_limit() -> None:
    """rank_by_stars respects the limit parameter."""
    from gitrank.rank.engine import rank_by_stars

    repos = [
        _make_repo(github_id=i, full_name=f"repo/{i}", stargazers_count=i * 100)
        for i in range(1, 11)
    ]

    result = rank_by_stars(repos, limit=5)
    assert len(result) == 5


# ---------------------------------------------------------------------------
# _calc_star_score
# ---------------------------------------------------------------------------


def test_calc_star_score_zero_max() -> None:
    """_calc_star_score returns 0.0 when max_stars is 0."""
    from gitrank.rank.engine import _calc_star_score

    assert _calc_star_score(0, 0) == 0.0
    assert _calc_star_score(100, 0) == 0.0


def test_calc_star_score_max_repo() -> None:
    """_calc_star_score returns 1.0 for the repo with max stars."""
    from gitrank.rank.engine import _calc_star_score

    score = _calc_star_score(1000, 1000)
    assert score == pytest.approx(1.0)


def test_calc_star_score_in_range() -> None:
    """_calc_star_score always returns a value in [0, 1]."""
    from gitrank.rank.engine import _calc_star_score

    max_stars = 10000
    for stars in [0, 1, 10, 100, 1000, 5000, 10000]:
        score = _calc_star_score(stars, max_stars)
        assert 0.0 <= score <= 1.0


# ---------------------------------------------------------------------------
# _calc_growth_score
# ---------------------------------------------------------------------------


def test_calc_growth_score_cold_start() -> None:
    """_calc_growth_score returns 0.5 when no star_history is provided."""
    from gitrank.rank.engine import _calc_growth_score

    repo = _make_repo(github_id=1, stargazers_count=500)
    score = _calc_growth_score(repo, max_growth=100.0, star_history=None)
    assert score == 0.5


def test_calc_growth_score_with_history() -> None:
    """_calc_growth_score with star_history calculates growth correctly."""
    from gitrank.rank.engine import _calc_growth_score

    repo = _make_repo(github_id=1, stargazers_count=550)
    # 4 monthly snapshots: [100, 250, 400, 550]
    # growth = (550 - 100) / 3 months = 150 stars/month
    star_history = {1: [100, 250, 400, 550]}

    # max_growth = 150, so score = log10(151)/log10(151) = 1.0
    score = _calc_growth_score(repo, max_growth=150.0, star_history=star_history)
    assert score == pytest.approx(1.0)

    # With a larger max_growth, score should be < 1.0
    score2 = _calc_growth_score(repo, max_growth=500.0, star_history=star_history)
    assert 0.0 < score2 < 1.0


def test_calc_growth_score_no_history_for_repo() -> None:
    """_calc_growth_score returns 0.5 when repo not in star_history."""
    from gitrank.rank.engine import _calc_growth_score

    repo = _make_repo(github_id=99, stargazers_count=500)
    star_history = {1: [100, 200, 300]}  # different repo

    score = _calc_growth_score(repo, max_growth=100.0, star_history=star_history)
    assert score == 0.5


# ---------------------------------------------------------------------------
# _calc_activity_score
# ---------------------------------------------------------------------------


def test_calc_activity_score_recent_push() -> None:
    """_calc_activity_score returns high score for recently pushed repo."""
    from gitrank.rank.engine import _calc_activity_score

    now = datetime.now(timezone.utc)
    repo = _make_repo(github_id=1, pushed_at=now)

    score = _calc_activity_score(repo, window_days=365)
    # Pushed just now, so days_since ≈ 0, score ≈ 1.0
    assert score == pytest.approx(1.0, abs=0.01)


def test_calc_activity_score_old_push() -> None:
    """_calc_activity_score returns low score for repo pushed long ago."""
    from gitrank.rank.engine import _calc_activity_score

    window_days = 365
    old_date = datetime.now(timezone.utc) - timedelta(days=window_days)
    repo = _make_repo(github_id=1, pushed_at=old_date)

    score = _calc_activity_score(repo, window_days=window_days)
    # Pushed window_days ago, score ≈ 0.0
    assert score == pytest.approx(0.0, abs=0.01)


def test_calc_activity_score_clamped() -> None:
    """_calc_activity_score clamps to [0, 1] for extreme values."""
    from gitrank.rank.engine import _calc_activity_score

    window_days = 30
    # Pushed 2 years ago — score should clamp to 0, not go negative
    very_old = datetime.now(timezone.utc) - timedelta(days=730)
    repo = _make_repo(github_id=1, pushed_at=very_old)

    score = _calc_activity_score(repo, window_days=window_days)
    assert score == 0.0


# ---------------------------------------------------------------------------
# rank_by_composite
# ---------------------------------------------------------------------------


def test_rank_by_composite_orders_by_composite_descending() -> None:
    """rank_by_composite sorts by composite_score descending."""
    from gitrank.rank.engine import rank_by_composite

    now = datetime.now(timezone.utc)
    repos = [
        Repository(
            id=1,
            full_name="low/repo",
            stargazers_count=10,
            created_at=now,
            updated_at=now,
            pushed_at=now - timedelta(days=300),
        ),
        Repository(
            id=2,
            full_name="high/repo",
            stargazers_count=5000,
            created_at=now,
            updated_at=now,
            pushed_at=now,
        ),
        Repository(
            id=3,
            full_name="mid/repo",
            stargazers_count=1000,
            created_at=now,
            updated_at=now,
            pushed_at=now - timedelta(days=30),
        ),
    ]

    result = rank_by_composite(repos, window_days=365)

    assert len(result) == 3
    assert result[0].rank == 1
    assert result[1].rank == 2
    assert result[2].rank == 3
    # Check descending order
    assert result[0].composite_score >= result[1].composite_score >= result[2].composite_score
    # highest star + most active = highest composite
    assert result[0].repo.full_name == "high/repo"


def test_rank_by_composite_respects_limit() -> None:
    """rank_by_composite respects the limit parameter."""
    from gitrank.rank.engine import rank_by_composite

    now = datetime.now(timezone.utc)
    repos = [
        Repository(
            id=i,
            full_name=f"repo/{i}",
            stargazers_count=i * 100,
            created_at=now,
            updated_at=now,
            pushed_at=now,
        )
        for i in range(1, 11)
    ]

    result = rank_by_composite(repos, window_days=365, limit=3)
    assert len(result) == 3


def test_rank_by_composite_scores_in_range() -> None:
    """All scores in rank_by_composite output are in [0, 1]."""
    from gitrank.rank.engine import rank_by_composite

    now = datetime.now(timezone.utc)
    repos = [
        Repository(
            id=1,
            full_name="a/repo",
            stargazers_count=100,
            created_at=now,
            updated_at=now,
            pushed_at=now,
        ),
        Repository(
            id=2,
            full_name="b/repo",
            stargazers_count=5000,
            created_at=now,
            updated_at=now,
            pushed_at=now - timedelta(days=180),
        ),
    ]

    result = rank_by_composite(repos, window_days=365)

    for ranked in result:
        assert 0.0 <= ranked.stars_score <= 1.0
        assert 0.0 <= ranked.growth_score <= 1.0
        assert 0.0 <= ranked.activity_score <= 1.0
        assert 0.0 <= ranked.composite_score <= 1.0
