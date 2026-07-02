"""Test TUI Settings screen and sub-pickers."""

import json
import tempfile
from pathlib import Path

import pytest

from gitrank.settings import DEFAULT_CONFIG, Settings
from gitrank.tui.screens.settings import (
    SettingsScreen,
    _TopicPickerScreen,
    _TimePickerScreen,
    _SortPickerScreen,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_list_items_from_screen(screen):
    """Recursively collect all ListItem widgets from a Screen's compose tree."""
    from textual.widgets import ListItem

    items = []
    for w in list(screen.compose()):
        if isinstance(w, ListItem):
            items.append(w)
        for child in list(getattr(w, "children", [])):
            if isinstance(child, ListItem):
                items.append(child)
        for child in list(getattr(w, "_pending_children", [])):
            if isinstance(child, ListItem):
                items.append(child)
    return items


def _get_static_labels_from_items(items):
    """Extract Static text labels from a list of ListItem widgets."""
    from textual.widgets import Static

    labels = []
    for item in items:
        for child in list(getattr(item, "_pending_children", [])):
            if isinstance(child, Static):
                content = getattr(child, "_Static__content", None)
                if content:
                    labels.append(content)
    return labels


# ---------------------------------------------------------------------------
# 1. test_settings_screen_displays_current_values
# ---------------------------------------------------------------------------


def test_settings_screen_displays_current_values() -> None:
    """SettingsScreen compose produces a Static with id 'current_settings'."""
    screen = SettingsScreen()
    from textual.widgets import Static

    found = False
    for w in list(screen.compose()):
        if isinstance(w, Static) and w.id == "current_settings":
            found = True
            break
    assert found, "Expected Static widget with id='current_settings' in SettingsScreen"


# ---------------------------------------------------------------------------
# 2. test_settings_screen_has_setting_options
# ---------------------------------------------------------------------------


def test_settings_screen_has_setting_options() -> None:
    """SettingsScreen ListView contains Topic, Time Window, Sort Method items."""
    screen = SettingsScreen()
    items = _get_list_items_from_screen(screen)
    labels = _get_static_labels_from_items(items)

    assert len(items) == 3, (
        f"Expected 3 ListItems in SettingsScreen, got {len(items)}"
    )
    assert "Topic" in labels, f"Expected 'Topic' in labels, got {labels}"
    assert "Time Window" in labels, f"Expected 'Time Window' in labels, got {labels}"
    assert "Sort Method" in labels, f"Expected 'Sort Method' in labels, got {labels}"


# ---------------------------------------------------------------------------
# 3. test_topic_picker_screen_exists
# ---------------------------------------------------------------------------


def test_topic_picker_screen_exists() -> None:
    """_TopicPickerScreen is importable, composes, and contains topic options."""
    screen = _TopicPickerScreen()
    assert screen is not None

    widgets = list(screen.compose())
    assert len(widgets) > 0, "Expected _TopicPickerScreen to compose widgets"

    items = _get_list_items_from_screen(screen)
    labels = _get_static_labels_from_items(items)

    assert len(labels) > 0, "Expected topic option labels in the picker"
    # ai should be one of the preset topics
    assert "ai" in labels, f"Expected 'ai' in topic labels, got {labels}"


# ---------------------------------------------------------------------------
# 4. test_save_updates_settings
# ---------------------------------------------------------------------------


def test_save_updates_settings() -> None:
    """Selecting a setting via settings.update changes the Settings data on disk."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir)
        settings = Settings(config_dir=config_dir)
        settings.load()  # initialize with defaults

        # Simulate what the topic picker would do on selection
        settings.update("topic", "machine-learning")

        # Verify the data was saved to the in-memory state
        result = settings.load()
        assert result["topic"] == "machine-learning"
        assert result["time_window"] == DEFAULT_CONFIG["time_window"]
        assert result["sort"] == DEFAULT_CONFIG["sort"]

        # Verify the config file was created and contains the update
        config_file = config_dir / "config.json"
        assert config_file.exists()
        raw = json.loads(config_file.read_text(encoding="utf-8"))
        assert raw["topic"] == "machine-learning"


# ---------------------------------------------------------------------------
# Additional coverage tests
# ---------------------------------------------------------------------------


def test_settings_screen_has_escape_binding() -> None:
    """SettingsScreen has an escape binding that maps to pop_screen."""
    screen = SettingsScreen()
    bindings = {b[0]: b[1] for b in screen.BINDINGS}
    assert "escape" in bindings, "Expected 'escape' key binding"
    assert bindings["escape"] == "pop_screen"


def test_topic_picker_has_escape_binding() -> None:
    """_TopicPickerScreen has an escape binding for back navigation."""
    screen = _TopicPickerScreen()
    bindings = {b[0]: b[1] for b in screen.BINDINGS}
    assert "escape" in bindings
    assert bindings["escape"] == "pop_screen"


def test_time_picker_screen_exists() -> None:
    """_TimePickerScreen is importable, composes, and contains time options."""
    screen = _TimePickerScreen()
    assert screen is not None

    widgets = list(screen.compose())
    assert len(widgets) > 0

    items = _get_list_items_from_screen(screen)
    labels = _get_static_labels_from_items(items)
    assert len(labels) > 0
    assert "All Time" in labels, f"Expected 'All Time' in labels, got {labels}"


def test_sort_picker_screen_exists() -> None:
    """_SortPickerScreen is importable, composes, and contains Stars/Composite."""
    screen = _SortPickerScreen()
    assert screen is not None

    widgets = list(screen.compose())
    assert len(widgets) > 0

    items = _get_list_items_from_screen(screen)
    labels = _get_static_labels_from_items(items)
    assert len(labels) == 2, f"Expected 2 sort options, got {len(labels)}"
    assert "Stars" in labels, f"Expected 'Stars' in labels, got {labels}"
    assert "Composite" in labels, f"Expected 'Composite' in labels, got {labels}"
