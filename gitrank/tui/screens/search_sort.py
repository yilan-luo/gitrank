"""Sort method selection screen — Step 3 of the search wizard."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, ListView, ListItem, Static


class SearchSortScreen(Screen):
    """Step 3: Select sort method (Stars or Composite)."""

    BINDINGS = [
        ("enter", "select", "Select"),
        ("escape", "pop_screen", "Back"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Step 3: Select Sort Method", classes="title")
        yield ListView(
            ListItem(Static("Stars")),
            ListItem(Static("Composite")),
        )
        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle Enter on a sort option."""
        item = event.item
        if item is not None:
            for child in getattr(item, "_pending_children", []):
                if isinstance(child, Static):
                    label = getattr(child, "_Static__content", None)
                    if label:
                        self._navigate_with_sort(str(label))
                        return

    def _navigate_with_sort(self, label: str) -> None:
        """Store the sort method in SearchState and trigger the search."""
        sort_map = {
            "Stars": "stars",
            "Composite": "composite",
        }
        sort = sort_map.get(label, "stars")
        app = self.app
        if hasattr(app, "search_state"):
            app.search_state.sort = sort
        from gitrank.tui.screens.loading import LoadingScreen

        self.app.push_screen(LoadingScreen())

    def action_pop_screen(self) -> None:
        """Go back to the time window selection screen."""
        self.app.pop_screen()
