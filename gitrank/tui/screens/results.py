"""Results screen with ranked repository table."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer, Header

from gitrank.api.models import RankedRepo
from gitrank.tui.widgets.repo_table import RepoTable


class ResultsScreen(Screen):
    """Displays ranked search results in a DataTable.

    Enter on a row pushes RepoDetailScreen.
    Escape pops back to the search wizard.
    """

    BINDINGS = [
        ("enter", "select", "Details"),
        ("escape", "pop_screen", "Back"),
    ]

    def __init__(self, results: list[RankedRepo]) -> None:
        super().__init__()
        self.results = results

    def compose(self) -> ComposeResult:
        yield Header()
        yield RepoTable(id="results_table")
        yield Footer()

    def on_mount(self) -> None:
        """Populate the table once the screen is mounted."""
        table = self.query_one("#results_table", RepoTable)
        table.populate(self.results)

    def action_select(self) -> None:
        """Handle Enter - push detail screen for the selected repo."""
        table = self.query_one("#results_table", RepoTable)
        repo = table.get_selected_repo()
        if repo is not None:
            from gitrank.tui.widgets.repo_detail import RepoDetailScreen

            self.app.push_screen(RepoDetailScreen(repo))

    def action_pop_screen(self) -> None:
        """Handle Escape - go back to the search wizard."""
        self.app.pop_screen()
