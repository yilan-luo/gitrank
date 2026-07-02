"""Loading screen with progress bar and background search."""

from __future__ import annotations

from datetime import date, timedelta

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, ProgressBar, Static

from gitrank.api.client import GitHubClient
from gitrank.api.models import SearchParams
from gitrank.cache.db import CacheDB
from gitrank.orchestrator import QueryOrchestrator


class LoadingScreen(Screen):
    """Loading screen shown while the GitHub search is in progress.

    Displays an indeterminate progress bar and status text.  The search
    runs in a background worker so the UI stays responsive.
    """

    BINDINGS = [
        ("escape", "pop_screen", "Back"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Searching GitHub...", id="status")
        yield ProgressBar(show_eta=False)

    def on_mount(self) -> None:
        """Kick off the background search worker."""
        self.run_worker(self._do_search(), exclusive=True)

    # ------------------------------------------------------------------
    # Background search
    # ------------------------------------------------------------------

    async def _do_search(self) -> None:
        """Build SearchParams, execute the orchestrator, then push results."""
        try:
            app = self.app
            state = app.search_state

            today = date.today()
            date_start, date_end = self._resolve_dates(state, today)

            params = SearchParams(
                topic=state.topic,
                date_start=date_start,
                date_end=date_end,
                sort=state.sort,
            )

            cache = getattr(app, "cache_db", None) or CacheDB()
            client = getattr(app, "github_client", None) or GitHubClient()

            orchestrator = QueryOrchestrator(cache=cache, client=client)
            results = await orchestrator.execute(params)

            if self._is_active():
                from gitrank.tui.screens.results import ResultsScreen

                self.app.pop_screen()
                self.app.push_screen(ResultsScreen(results))

        except Exception as exc:
            if self._is_active():
                self.query_one("#status", Static).update(
                    f"Error: {exc}. Press Esc to go back."
                )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_dates(state, today: date) -> tuple[date, date]:
        """Convert a SearchState time_window into a concrete date range."""
        time_window = getattr(state, "time_window", "all")

        if time_window == "last_month":
            return today - timedelta(days=30), today
        elif time_window == "last_3_months":
            return today - timedelta(days=90), today
        elif time_window == "last_year":
            return today - timedelta(days=365), today
        elif time_window == "custom":
            since = (
                date.fromisoformat(state.custom_since)
                if state.custom_since
                else today - timedelta(days=365)
            )
            until = (
                date.fromisoformat(state.custom_until)
                if state.custom_until
                else today
            )
            return since, until
        else:
            # "all" or unknown
            return date(2008, 1, 1), today

    def _is_active(self) -> bool:
        """Return True if the screen is still mounted and visible."""
        try:
            return self.is_mounted
        except Exception:
            return False
