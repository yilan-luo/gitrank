"""SQLite cache layer for persisting GitHub repository data and star snapshots."""

import json
import sqlite3
from datetime import date, datetime, timedelta, timezone
from typing import List, Optional

from gitrank.api.models import Repository, StarSnapshot


class CacheDB:
    """SQLite-backed cache for repositories and star history."""

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def initialize(self) -> None:
        """Create tables if they don't exist."""
        if self.conn is not None:
            return
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS repositories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                github_id INTEGER UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                description TEXT,
                language TEXT,
                topics TEXT,
                stargazers_count INTEGER NOT NULL,
                forks_count INTEGER DEFAULT 0,
                open_issues_count INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                pushed_at TEXT NOT NULL,
                html_url TEXT,
                archived INTEGER DEFAULT 0,
                cached_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS star_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                github_id INTEGER NOT NULL,
                stargazers_count INTEGER NOT NULL,
                recorded_at TEXT NOT NULL
            );
        """)
        self.conn.commit()

    def close(self) -> None:
        """Close the database connection."""
        if self.conn is not None:
            self.conn.close()
            self.conn = None

    # ------------------------------------------------------------------
    # Repository CRUD
    # ------------------------------------------------------------------

    def upsert_repository(self, repo: Repository) -> None:
        """Insert or update a repository record."""
        self.conn.execute(
            """
            INSERT OR REPLACE INTO repositories
                (github_id, full_name, description, language, topics,
                 stargazers_count, forks_count, open_issues_count,
                 created_at, updated_at, pushed_at, html_url, archived, cached_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                repo.id,
                repo.full_name,
                repo.description,
                repo.language,
                json.dumps(repo.topics),
                repo.stargazers_count,
                repo.forks_count,
                repo.open_issues_count,
                repo.created_at.isoformat(),
                repo.updated_at.isoformat(),
                repo.pushed_at.isoformat(),
                repo.html_url,
                1 if repo.archived else 0,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self.conn.commit()

    def get_repository(self, github_id: int) -> Optional[Repository]:
        """Get a single repository by github_id."""
        row = self.conn.execute(
            "SELECT * FROM repositories WHERE github_id = ?", (github_id,)
        ).fetchone()
        if row is None:
            return None
        return self._row_to_repo(row)

    def get_repositories_by_date(
        self,
        date_start: date,
        date_end: date,
        topic: Optional[str] = None,
    ) -> List[Repository]:
        """Get repositories created within date range, optionally filtered by topic."""
        if topic is not None:
            rows = self.conn.execute(
                """
                SELECT * FROM repositories
                WHERE date(created_at) >= ? AND date(created_at) <= ?
                  AND topics LIKE ?
                """,
                (date_start.isoformat(), date_end.isoformat(), f'%"{topic}"%'),
            ).fetchall()
        else:
            rows = self.conn.execute(
                """
                SELECT * FROM repositories
                WHERE date(created_at) >= ? AND date(created_at) <= ?
                """,
                (date_start.isoformat(), date_end.isoformat()),
            ).fetchall()
        return [self._row_to_repo(r) for r in rows]

    # ------------------------------------------------------------------
    # Cache freshness
    # ------------------------------------------------------------------

    def cache_hit(self, topic: str, date_start: date, date_end: date) -> bool:
        """Check if a query is already cached (has results for the given params).

        Returns True when at least one non-stale repository matches the
        topic and date range.
        """
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
        row = self.conn.execute(
            """
            SELECT COUNT(*) AS cnt FROM repositories
            WHERE topics LIKE ?
              AND date(created_at) >= ? AND date(created_at) <= ?
              AND cached_at > ?
            """,
            (f'%"{topic}"%', date_start.isoformat(), date_end.isoformat(), cutoff),
        ).fetchone()
        return row["cnt"] > 0

    def refresh_repositories(self) -> None:
        """Remove stale entries (older than 24 hours)."""
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
        self.conn.execute(
            "DELETE FROM repositories WHERE cached_at <= ?", (cutoff,)
        )
        self.conn.commit()

    # ------------------------------------------------------------------
    # Star history
    # ------------------------------------------------------------------

    def record_snapshot(self, github_id: int, stargazers_count: int) -> None:
        """Record a star count snapshot in star_history."""
        self.conn.execute(
            "INSERT INTO star_history (github_id, stargazers_count, recorded_at) VALUES (?, ?, ?)",
            (github_id, stargazers_count, datetime.now(timezone.utc).isoformat()),
        )
        self.conn.commit()

    def get_snapshots(self, github_id: int) -> List[StarSnapshot]:
        """Get all star snapshots for a repository, ordered by recorded_at."""
        rows = self.conn.execute(
            "SELECT * FROM star_history WHERE github_id = ? ORDER BY recorded_at ASC",
            (github_id,),
        ).fetchall()
        return [
            StarSnapshot(
                github_id=r["github_id"],
                stargazers_count=r["stargazers_count"],
                recorded_at=datetime.fromisoformat(r["recorded_at"]),
            )
            for r in rows
        ]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _row_to_repo(self, row: sqlite3.Row) -> Repository:
        """Convert a sqlite3.Row back into a Repository model."""
        return Repository(
            id=row["github_id"],
            full_name=row["full_name"],
            description=row["description"],
            language=row["language"],
            topics=json.loads(row["topics"] or "[]"),
            stargazers_count=row["stargazers_count"],
            forks_count=row["forks_count"],
            open_issues_count=row["open_issues_count"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            pushed_at=datetime.fromisoformat(row["pushed_at"]),
            html_url=row["html_url"],
            archived=bool(row["archived"]),
        )
