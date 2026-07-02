from __future__ import annotations

"""Search topic selection screen — Step 1 of the search wizard."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, ListView, ListItem, Static, Input

from gitrank.tui.constants import PRESET_TOPICS


class SearchTopicScreen(Screen):
    """Step 1: Select a topic from presets or enter a custom one."""

    BINDINGS = [
        ("enter", "select", "Select"),
        ("escape", "pop_screen", "Back"),
    ]

    PRESET_TOPICS: list[str] = PRESET_TOPICS

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Step 1: Select a Topic", classes="title")
        yield ListView(
            *[ListItem(Static(topic)) for topic in self.PRESET_TOPICS],
        )
        yield Static("Or enter a custom topic:")
        yield Input(placeholder="e.g. blockchain, cli, visualization...", id="custom_topic")
        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle Enter on a preset topic item."""
        if event.item_index < len(self.PRESET_TOPICS):
            topic = self.PRESET_TOPICS[event.item_index]
            self._navigate_with_topic(topic)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter in the custom topic Input."""
        if event.input.id == "custom_topic" and event.value.strip():
            self._navigate_with_topic(event.value.strip())

    def _navigate_with_topic(self, topic: str) -> None:
        """Store the topic in SearchState and advance to Step 2."""
        app = self.app
        if hasattr(app, "search_state"):
            app.search_state.topic = topic
        from gitrank.tui.screens.search_time import SearchTimeScreen

        self.app.push_screen(SearchTimeScreen())

    def action_pop_screen(self) -> None:
        """Go back to the main menu."""
        self.app.pop_screen()
