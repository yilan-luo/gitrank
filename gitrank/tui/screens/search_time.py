"""Time window selection screen — Step 2 of the search wizard."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, ListView, ListItem, Static, Input


class SearchTimeScreen(Screen):
    """Step 2: Select a time window for the search."""

    BINDINGS = [
        ("enter", "select", "Select"),
        ("escape", "pop_screen", "Back"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Step 2: Select Time Window", classes="title")
        yield ListView(
            ListItem(Static("All Time")),
            ListItem(Static("Last Month")),
            ListItem(Static("Last 3 Months")),
            ListItem(Static("Last Year")),
            ListItem(Static("Custom")),
        )
        yield Static("Custom date range (YYYY-MM-DD):")
        yield Input(placeholder="Since (YYYY-MM-DD)", id="since_input")
        yield Input(placeholder="Until (YYYY-MM-DD)", id="until_input")
        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle Enter on a time window option."""
        item = event.item
        if item is not None:
            for child in getattr(item, "_pending_children", []):
                if isinstance(child, Static):
                    label = getattr(child, "_Static__content", None)
                    if label:
                        self._navigate_with_time(str(label))
                        return

    def _navigate_with_time(self, label: str) -> None:
        """Store the time window in SearchState and advance to Step 3."""
        time_map = {
            "All Time": "all",
            "Last Month": "last_month",
            "Last 3 Months": "last_3_months",
            "Last Year": "last_year",
            "Custom": "custom",
        }
        time_window = time_map.get(label, "all")
        app = self.app
        if hasattr(app, "search_state"):
            app.search_state.time_window = time_window
            if time_window == "custom":
                since_input = self.query_one("#since_input", Input)
                until_input = self.query_one("#until_input", Input)
                app.search_state.custom_since = since_input.value.strip() or None
                app.search_state.custom_until = until_input.value.strip() or None
        from gitrank.tui.screens.search_sort import SearchSortScreen

        self.app.push_screen(SearchSortScreen())

    def action_pop_screen(self) -> None:
        """Go back to the topic selection screen."""
        self.app.pop_screen()
