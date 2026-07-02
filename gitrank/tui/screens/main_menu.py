from __future__ import annotations

"""Main menu screen with Search, Settings, and Quit options."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, ListView, ListItem, Static


class MainMenuScreen(Screen):
    """Main menu with Search, Settings, and Quit options."""

    BINDINGS = [
        ("enter", "select", "Select"),
    ]

    MENU_ITEMS: list[tuple[str, str]] = [
        ("Search", "search"),
        ("Settings", "settings"),
        ("Quit", "quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("GitRank - GitHub Repository Ranking", classes="title")
        yield ListView(
            *[ListItem(Static(label)) for label, _ in self.MENU_ITEMS],
        )
        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle Enter on a menu item."""
        if event.item_index >= len(self.MENU_ITEMS):
            return

        _label, action = self.MENU_ITEMS[event.item_index]
        if action == "search":
            from gitrank.tui.screens.search_topic import SearchTopicScreen

            # Pre-fill search state from saved settings
            settings = self.app.settings
            settings_data = settings.data if settings.data else {}
            self.app.search_state.topic = settings_data.get("topic", "")
            self.app.search_state.time_window = settings_data.get(
                "time_window", "last_6_months"
            )
            self.app.search_state.sort = settings_data.get("sort", "stars")

            self.app.push_screen(SearchTopicScreen())
        elif action == "settings":
            from gitrank.tui.screens.settings import SettingsScreen

            self.app.push_screen(SettingsScreen())
        elif action == "quit":
            self.app.exit()
