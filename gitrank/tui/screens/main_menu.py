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

            self.app.push_screen(SearchTopicScreen())
        elif action == "settings":
            from gitrank.tui.screens.settings import SettingsScreen

            self.app.push_screen(SettingsScreen())
        elif action == "quit":
            self.app.exit()
