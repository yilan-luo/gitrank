"""Placeholder: Loading screen (coming soon)."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static


class LoadingScreen(Screen):
    """Loading/progress screen (placeholder)."""

    def compose(self) -> ComposeResult:
        yield Static("Loading - Coming Soon")
