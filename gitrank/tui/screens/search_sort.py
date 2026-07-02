from __future__ import annotations

"""Sort method selection screen — Step 3 of the search wizard."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, ListView, ListItem, Static

from gitrank.tui.constants import SORT_OPTIONS, SORT_LABELS


class SearchSortScreen(Screen):
    """Step 3: Select sort method (Stars or Composite)."""

    BINDINGS = [
        ("enter", "select", "Select"),
        ("escape", "pop_screen", "Back"),
    ]

    SORT_OPTIONS: list[str] = SORT_OPTIONS

    def on_mount(self) -> None:
        """Pre-highlight the sort method from saved settings."""
        app = self.app
        if hasattr(app, "search_state") and app.search_state.sort:
            try:
                idx = self.SORT_OPTIONS.index(app.search_state.sort)
                self.query_one(ListView).index = idx
            except ValueError:
                pass

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Step 3: Select Sort Method", classes="title")
        yield ListView(
            *[ListItem(Static(SORT_LABELS[opt])) for opt in self.SORT_OPTIONS],
        )
        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle Enter on a sort option."""
        if event.item_index < len(self.SORT_OPTIONS):
            sort = self.SORT_OPTIONS[event.item_index]
            self._navigate_with_sort(sort)

    def _navigate_with_sort(self, sort: str) -> None:
        """Store the sort method in SearchState and trigger the search."""
        app = self.app
        if hasattr(app, "search_state"):
            app.search_state.sort = sort
        from gitrank.tui.screens.loading import LoadingScreen

        self.app.push_screen(LoadingScreen())

    def action_pop_screen(self) -> None:
        """Go back to the time window selection screen."""
        self.app.pop_screen()
