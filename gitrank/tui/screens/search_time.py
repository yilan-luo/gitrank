"""Time window selection screen — Step 2 of the search wizard."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, ListView, ListItem, Static, Input

from gitrank.tui.constants import PRESET_TIME_WINDOWS, TIME_WINDOW_LABELS


class SearchTimeScreen(Screen):
    """Step 2: Select a time window for the search."""

    BINDINGS = [
        ("enter", "select", "Select"),
        ("escape", "pop_screen", "Back"),
    ]

    TIME_WINDOWS: list[str] = PRESET_TIME_WINDOWS

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Step 2: Select Time Window", classes="title")
        yield ListView(
            *[ListItem(Static(TIME_WINDOW_LABELS[tw])) for tw in self.TIME_WINDOWS],
        )
        yield Static("Custom date range (YYYY-MM-DD):")
        yield Input(placeholder="Since (YYYY-MM-DD)", id="since_input")
        yield Input(placeholder="Until (YYYY-MM-DD)", id="until_input")
        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle Enter on a time window option."""
        if event.item_index < len(self.TIME_WINDOWS):
            time_window = self.TIME_WINDOWS[event.item_index]
            self._navigate_with_time(time_window)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle date input submission (read when Custom is selected)."""
        pass  # Values are read from the Input widgets when navigating

    def _navigate_with_time(self, time_window: str) -> None:
        """Store the time window in SearchState and advance to Step 3."""
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
