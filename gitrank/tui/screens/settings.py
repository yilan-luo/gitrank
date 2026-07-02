"""Settings screen with sub-pickers for Topic, Time Window, and Sort Method."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, ListView, ListItem, Static

from gitrank.settings import Settings
from gitrank.tui.constants import (
    PRESET_TOPICS,
    PRESET_TIME_WINDOWS,
    SORT_OPTIONS,
    TIME_WINDOW_LABELS,
    SORT_LABELS,
)


# ---------------------------------------------------------------------------
# Sub-picker screens
# ---------------------------------------------------------------------------


class _TopicPickerScreen(Screen):
    """Sub-picker for selecting a default topic."""

    BINDINGS = [
        ("escape", "pop_screen", "Back"),
    ]

    TOPICS: list[str] = PRESET_TOPICS

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Select Default Topic", classes="title")
        yield ListView(
            *[ListItem(Static(topic)) for topic in self.TOPICS],
        )
        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Update the topic setting and dismiss."""
        topic = self.TOPICS[event.item_index]
        settings = Settings()
        settings.update("topic", topic)
        self.dismiss(topic)


class _TimePickerScreen(Screen):
    """Sub-picker for selecting a default time window."""

    BINDINGS = [
        ("escape", "pop_screen", "Back"),
    ]

    # Exclude "custom" — it does not make sense as a persistent default.
    TIME_OPTIONS: dict[str, str] = {
        k: TIME_WINDOW_LABELS[k] for k in PRESET_TIME_WINDOWS if k != "custom"
    }

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Select Default Time Window", classes="title")
        yield ListView(
            *[ListItem(Static(label)) for label in self.TIME_OPTIONS.values()],
        )
        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Update the time_window setting and dismiss."""
        key = list(self.TIME_OPTIONS.keys())[event.item_index]
        settings = Settings()
        settings.update("time_window", key)
        self.dismiss(key)


class _SortPickerScreen(Screen):
    """Sub-picker for selecting a default sort method."""

    BINDINGS = [
        ("escape", "pop_screen", "Back"),
    ]

    SORT_OPTIONS: dict[str, str] = {k: SORT_LABELS[k] for k in SORT_OPTIONS}

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Select Default Sort Method", classes="title")
        yield ListView(
            *[ListItem(Static(label)) for label in self.SORT_OPTIONS.values()],
        )
        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Update the sort setting and dismiss."""
        key = list(self.SORT_OPTIONS.keys())[event.item_index]
        settings = Settings()
        settings.update("sort", key)
        self.dismiss(key)


# ---------------------------------------------------------------------------
# Main Settings screen
# ---------------------------------------------------------------------------


class SettingsScreen(Screen):
    """Settings screen showing current defaults and allowing modification.

    Displays the current configuration values and provides a ListView so the
    user can pick which setting to modify.  Each selection pushes a sub-picker
    screen that writes the new value back to ``~/.gitrank/config.json``.
    """

    BINDINGS = [
        ("escape", "pop_screen", "Back"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Settings", classes="title")
        yield Static(id="current_settings")
        yield Static("Select a setting to modify:")
        yield ListView(
            ListItem(Static("Topic")),
            ListItem(Static("Time Window")),
            ListItem(Static("Sort Method")),
        )
        yield Footer()

    def on_mount(self) -> None:
        """Load current settings and update the display."""
        self._refresh_display()

    def _refresh_display(self) -> None:
        """Read settings from disk and update the current_settings widget."""
        settings = Settings()
        data = settings.load()
        current = self.query_one("#current_settings", Static)
        current.update(
            f"Topic: {data['topic']}  |  "
            f"Time Window: {data['time_window']}  |  "
            f"Sort: {data['sort']}"
        )

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Push the appropriate sub-picker based on the selected row."""
        if event.item_index == 0:
            self.app.push_screen(
                _TopicPickerScreen(), callback=self._on_sub_screen_done
            )
        elif event.item_index == 1:
            self.app.push_screen(
                _TimePickerScreen(), callback=self._on_sub_screen_done
            )
        elif event.item_index == 2:
            self.app.push_screen(
                _SortPickerScreen(), callback=self._on_sub_screen_done
            )

    def _on_sub_screen_done(self, _result) -> None:
        """Refresh the display after a sub-picker returns."""
        self._refresh_display()
