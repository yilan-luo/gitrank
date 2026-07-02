"""Tests for gitrank.cache.db -- CacheDB class."""

import json
import time
from datetime import date, datetime, timedelta, timezone
from typing import Optional

import pytest

from gitrank.api.models import Repository, StarSnapshot


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_repo(
    github_id: int = 1,
    full_name: str = "owner/repo",
    description: Optional[str] = "A test repo",
    language: Optional[str] = "Python",
    topics: Optional[list] = None,
    stargazers_count: int = 100,
    forks_count: int = 10,
    open_issues_count: int = 5,
    created_at: Optional[datetime] = None,
    updated_at: Optional[datetime] = None,
    pushed_at: Optional[datetime] = None,
    html_url: Optional[str] = "https://github.com/owner/repo",
    archived: bool = False,
) -> Repository:
    """Build a Repository model with sensible defaults."""
    if topics is None:
        topics = ["python", "web"]
    now = datetime(2025, 7, 1, 12, 0, 0)
    return Repository(
        id=github_id,
        full_name=full_name,
        description=description,
        language=language,
        topics=topics,
        stargazers_count=stargazers_count,
        forks_count=forks_count,
        open_issues_count=open_issues_count,
        created_at=created_at or now,
        updated_at=updated_at or now,
        pushed_at=pushed_at or now,
        html_url=html_url,
        archived=archived,
    )


# ---------------------------------------------------------------------------
# 1. initialize() creates both tables
# ---------------------------------------------------------------------------

def test_initialize_creates_tables(temp_db) -> None:
    """After initialize(), both 'repositories' and 'star_history' tables exist."""
    cursor = temp_db.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tables = [row[0] for row in cursor.fetchall()]
    assert "repositories" in tables
    assert "star_history" in tables


# ---------------------------------------------------------------------------
# 2. upsert_repository() inserts a new repo
# ---------------------------------------------------------------------------

def test_upsert_inserts_new_repo(temp_db) -> None:
    """upsert_repository() inserts a new repository record."""
    repo = make_repo(github_id=12345, full_name="test/repo", stargazers_count=42)

    temp_db.upsert_repository(repo)

    row = temp_db.conn.execute(
        "SELECT * FROM repositories WHERE github_id = ?", (12345,)
    ).fetchone()
    assert row is not None
    assert row["github_id"] == 12345
    assert row["full_name"] == "test/repo"
    assert row["description"] == "A test repo"
    assert row["language"] == "Python"
    assert json.loads(row["topics"]) == ["python", "web"]
    assert row["stargazers_count"] == 42
    assert row["forks_count"] == 10
    assert row["open_issues_count"] == 5
    assert row["html_url"] == "https://github.com/owner/repo"
    assert row["archived"] == 0
    assert row["cached_at"] is not None


# ---------------------------------------------------------------------------
# 3. upsert_repository() updates an existing repo (same github_id)
# ---------------------------------------------------------------------------

def test_upsert_updates_existing_repo(temp_db) -> None:
    """upsert_repository() updates fields when github_id already exists."""
    repo = make_repo(github_id=999, full_name="old/name", stargazers_count=10)

    temp_db.upsert_repository(repo)

    # Same github_id, different fields
    updated = make_repo(github_id=999, full_name="new/name", stargazers_count=500)
    temp_db.upsert_repository(updated)

    # Should still be exactly 1 row
    rows = temp_db.conn.execute(
        "SELECT * FROM repositories WHERE github_id = ?", (999,)
    ).fetchall()
    assert len(rows) == 1
    assert rows[0]["full_name"] == "new/name"
    assert rows[0]["stargazers_count"] == 500


# ---------------------------------------------------------------------------
# 4. get_repository() returns a repo by github_id
# ---------------------------------------------------------------------------

def test_get_repository_returns_repo(temp_db) -> None:
    """get_repository() returns a Repository object for a known github_id."""
    repo = make_repo(github_id=42, full_name="meaning/of-life")
    temp_db.upsert_repository(repo)

    result = temp_db.get_repository(42)

    assert result is not None
    assert isinstance(result, Repository)
    assert result.id == 42
    assert result.full_name == "meaning/of-life"
    assert result.topics == ["python", "web"]
    assert result.archived is False


# ---------------------------------------------------------------------------
# 5. get_repository() returns None for missing id
# ---------------------------------------------------------------------------

def test_get_repository_returns_none_for_missing(temp_db) -> None:
    """get_repository() returns None when github_id doesn't exist."""
    result = temp_db.get_repository(99999)
    assert result is None


# ---------------------------------------------------------------------------
# 6. get_repositories_by_date() filters by date range
# ---------------------------------------------------------------------------

def test_get_repositories_by_date_filters_by_date_range(temp_db) -> None:
    """get_repositories_by_date() only returns repos within the date range."""
    # Repo created in March
    early = make_repo(
        github_id=1,
        full_name="early/repo",
        created_at=datetime(2024, 3, 15, 10, 0, 0),
    )
    # Repo created in June
    late = make_repo(
        github_id=2,
        full_name="late/repo",
        created_at=datetime(2024, 6, 15, 10, 0, 0),
    )
    temp_db.upsert_repository(early)
    temp_db.upsert_repository(late)

    results = temp_db.get_repositories_by_date(
        date_start=date(2024, 6, 1),
        date_end=date(2024, 6, 30),
    )

    assert len(results) == 1
    assert results[0].full_name == "late/repo"


# ---------------------------------------------------------------------------
# 7. get_repositories_by_date() filters by topic
# ---------------------------------------------------------------------------

def test_get_repositories_by_date_filters_by_topic(temp_db) -> None:
    """get_repositories_by_date() only returns repos matching the given topic."""
    rust_repo = make_repo(
        github_id=10,
        full_name="rust-lang/rust",
        topics=["rust", "systems"],
        created_at=datetime(2024, 7, 1, 10, 0, 0),
    )
    py_repo = make_repo(
        github_id=20,
        full_name="python/cpython",
        topics=["python", "runtime"],
        created_at=datetime(2024, 7, 5, 10, 0, 0),
    )
    temp_db.upsert_repository(rust_repo)
    temp_db.upsert_repository(py_repo)

    # Filter by topic "rust" within a wide date range
    results = temp_db.get_repositories_by_date(
        date_start=date(2024, 1, 1),
        date_end=date(2024, 12, 31),
        topic="rust",
    )

    assert len(results) == 1
    assert results[0].full_name == "rust-lang/rust"


# ---------------------------------------------------------------------------
# 8. cache_hit() returns False for uncached query
# ---------------------------------------------------------------------------

def test_cache_hit_returns_false_for_uncached(temp_db) -> None:
    """cache_hit() returns False when no repos match the query."""
    # Empty database
    result = temp_db.cache_hit(
        topic="python",
        date_start=date(2024, 1, 1),
        date_end=date(2024, 12, 31),
    )
    assert result is False


# ---------------------------------------------------------------------------
# 9. cache_hit() returns True after repos are cached
# ---------------------------------------------------------------------------

def test_cache_hit_returns_true_after_caching(temp_db) -> None:
    """cache_hit() returns True when matching repos exist in cache."""
    repo = make_repo(
        github_id=77,
        full_name="trending/project",
        topics=["machine-learning", "ai"],
        created_at=datetime(2024, 5, 10, 10, 0, 0),
    )
    temp_db.upsert_repository(repo)

    result = temp_db.cache_hit(
        topic="machine-learning",
        date_start=date(2024, 1, 1),
        date_end=date(2024, 12, 31),
    )
    assert result is True


# ---------------------------------------------------------------------------
# 10. record_snapshot() records a star count
# ---------------------------------------------------------------------------

def test_record_snapshot_records_star_count(temp_db) -> None:
    """record_snapshot() inserts a row into star_history."""
    snapshot_time = datetime(2025, 7, 1, 12, 0, 0)

    temp_db.record_snapshot(github_id=100, stargazers_count=500)

    rows = temp_db.conn.execute(
        "SELECT * FROM star_history WHERE github_id = ?", (100,)
    ).fetchall()
    assert len(rows) == 1
    assert rows[0]["github_id"] == 100
    assert rows[0]["stargazers_count"] == 500
    assert rows[0]["recorded_at"] is not None


# ---------------------------------------------------------------------------
# 11. get_snapshots() returns snapshots ordered by time
# ---------------------------------------------------------------------------

def test_get_snapshots_returns_ordered(temp_db) -> None:
    """get_snapshots() returns star snapshots ordered by recorded_at ascending."""
    t1 = datetime(2025, 6, 1, 12, 0, 0)
    t2 = datetime(2025, 6, 15, 12, 0, 0)
    t3 = datetime(2025, 7, 1, 12, 0, 0)

    # Insert out of order
    temp_db.conn.execute(
        "INSERT INTO star_history (github_id, stargazers_count, recorded_at) VALUES (?, ?, ?)",
        (200, 300, t2.isoformat()),
    )
    temp_db.conn.execute(
        "INSERT INTO star_history (github_id, stargazers_count, recorded_at) VALUES (?, ?, ?)",
        (200, 100, t1.isoformat()),
    )
    temp_db.conn.execute(
        "INSERT INTO star_history (github_id, stargazers_count, recorded_at) VALUES (?, ?, ?)",
        (200, 500, t3.isoformat()),
    )

    snapshots = temp_db.get_snapshots(200)

    assert len(snapshots) == 3
    assert snapshots[0].stargazers_count == 100  # earliest
    assert snapshots[1].stargazers_count == 300
    assert snapshots[2].stargazers_count == 500  # latest


# ---------------------------------------------------------------------------
# 12. refresh_repositories() removes old entries
# ---------------------------------------------------------------------------

def test_refresh_repositories_removes_old_entries(temp_db) -> None:
    """refresh_repositories() removes entries older than 24 hours."""
    recent = make_repo(github_id=1, full_name="recent/repo")
    old = make_repo(github_id=2, full_name="old/repo")

    temp_db.upsert_repository(recent)
    temp_db.upsert_repository(old)

    # Manually set old repo's cached_at to 48 hours ago
    stale_time = datetime.now(timezone.utc) - timedelta(hours=48)
    temp_db.conn.execute(
        "UPDATE repositories SET cached_at = ? WHERE github_id = ?",
        (stale_time.isoformat(), 2),
    )
    temp_db.conn.commit()

    temp_db.refresh_repositories()

    # Recent repo should still exist
    assert temp_db.get_repository(1) is not None
    # Old repo should be gone
    assert temp_db.get_repository(2) is None
