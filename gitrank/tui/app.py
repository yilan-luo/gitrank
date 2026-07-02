"""GitRankApp - the main Textual application for GitHub repository ranking."""

from textual.app import App
from textual.binding import Binding


class GitRankApp(App):
    """GitHub repository ranking TUI application."""

    CSS = """
    Screen {
        align: center middle;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
    ]

    def on_mount(self) -> None:
        """Push the main menu screen on startup."""
        from gitrank.tui.screens.main_menu import MainMenuScreen

        self.push_screen(MainMenuScreen())
