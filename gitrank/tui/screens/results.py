"""Placeholder: Results screen (coming soon)."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static


class ResultsScreen(Screen):
    """Results display screen (placeholder)."""

    def compose(self) -> ComposeResult:
        yield Static("Results - Coming Soon")
