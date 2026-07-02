"""RepoTable widget - DataTable wrapper for ranked repository display."""

from __future__ import annotations

from textual.widgets import DataTable

from gitrank.api.models import RankedRepo


class RepoTable(DataTable):
    """A DataTable specialized for displaying RankedRepo results.

    Provides ``populate()`` to fill rows from ranked results and
    ``get_selected_repo()`` to retrieve the currently highlighted repo.
    """

    def on_mount(self) -> None:
        """Set up columns when the widget is mounted."""
        self._ensure_columns()
        self._repos: list[RankedRepo] = []

    def _ensure_columns(self) -> None:
        """Add columns if they haven't been added yet (safe for unmounted tests)."""
        if not hasattr(self, "_columns_added"):
            self._columns_added = True
            self.add_columns(
                "Rank", "Repository", "Stars", "Growth", "Language", "Description"
            )

    def populate(self, repos: list[RankedRepo]) -> None:
        """Fill the table from a list of ranked repos.

        Args:
            repos: Ranked search results to display.
        """
        self._ensure_columns()
        self.clear()
        self._repos = repos
        for r in repos:
            self.add_row(
                str(r.rank),
                r.repo.full_name,
                str(r.repo.stargazers_count),
                f"{r.growth_per_month:.1f}/mo",
                r.repo.language or "",
                r.repo.description or "",
            )

    def get_selected_repo(self) -> RankedRepo | None:
        """Return the currently highlighted RankedRepo, or None if nothing is selected.

        Returns:
            The RankedRepo at the cursor row, or None.
        """
        if not self._repos:
            return None
        row = self.cursor_row
        if row < 0 or row >= len(self._repos):
            return None
        return self._repos[row]
