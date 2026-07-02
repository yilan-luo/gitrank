"""Placeholder: Settings screen (coming soon)."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static


class SettingsScreen(Screen):
    """Settings configuration screen (placeholder)."""

    def compose(self) -> ComposeResult:
        yield Static("Settings - Coming Soon")
