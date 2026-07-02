"""Main menu screen with Search, Settings, and Quit options."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, ListView, ListItem, Static


class MainMenuScreen(Screen):
    """Main menu with Search, Settings, and Quit options."""

    BINDINGS = [
        ("enter", "select", "Select"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("GitRank - GitHub Repository Ranking", classes="title")
        yield ListView(
            ListItem(Static("Search")),
            ListItem(Static("Settings")),
            ListItem(Static("Quit")),
        )
        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle Enter on a menu item."""
        # Navigate based on selected item index
        pass
