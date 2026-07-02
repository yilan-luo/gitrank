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
        import os

        from gitrank.api.client import GitHubClient
        from gitrank.cache.db import CacheDB
        from gitrank.settings import Settings
        from gitrank.tui.screens.main_menu import MainMenuScreen
        from gitrank.tui.state import SearchState

        self.settings = Settings()
        self.settings.load()

        # Pre-create and initialize cache so LoadingScreen can reuse it.
        cache_dir = Settings().config_dir
        cache_path = cache_dir / "cache.db"
        cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_db = CacheDB(db_path=str(cache_path))
        self.cache_db.initialize()

        self.github_client = GitHubClient(token=os.environ.get("GITHUB_TOKEN"))

        self.search_state = SearchState()
        self.push_screen(MainMenuScreen())

    def on_unmount(self) -> None:
        """Clean up resources on app shutdown."""
        if hasattr(self, "github_client"):
            try:
                import asyncio

                asyncio.ensure_future(self.github_client.aclose())
            except Exception:
                pass
        if hasattr(self, "cache_db"):
            try:
                self.cache_db.close()
            except Exception:
                pass
