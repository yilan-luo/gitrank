"""Test TUI app base, state management, and main menu."""

import pytest

from gitrank.tui.state import SearchState
from gitrank.tui.app import GitRankApp
from gitrank.tui.screens.main_menu import MainMenuScreen


class TestSearchState:
    """Tests for the SearchState dataclass."""

    def test_search_state_defaults(self) -> None:
        """SearchState has correct default values."""
        state = SearchState()
        assert state.topic == ""
        assert state.time_window == "last_6_months"
        assert state.custom_since is None
        assert state.custom_until is None
        assert state.sort == "stars"

    def test_search_state_can_set_fields(self) -> None:
        """SearchState fields can be set explicitly."""
        state = SearchState(
            topic="machine-learning",
            time_window="last_month",
            custom_since="2026-01-01",
            custom_until="2026-06-30",
            sort="composite",
        )
        assert state.topic == "machine-learning"
        assert state.time_window == "last_month"
        assert state.custom_since == "2026-01-01"
        assert state.custom_until == "2026-06-30"
        assert state.sort == "composite"


class TestGitRankApp:
    """Tests for the GitRankApp Textual application."""

    def test_app_has_quit_binding(self) -> None:
        """GitRankApp has a 'q' binding for quit."""
        app = GitRankApp()
        bindings = {binding.key: binding.action for binding in app.BINDINGS}
        assert "q" in bindings, "Expected 'q' key binding"
        assert bindings["q"] == "quit", "Expected 'q' to map to 'quit' action"

    def test_app_mounts_main_menu(self) -> None:
        """GitRankApp.on_mount pushes MainMenuScreen."""
        app = GitRankApp()
        # Verify that the app has the on_mount method that references MainMenuScreen
        import inspect
        source = inspect.getsource(app.on_mount)
        assert "MainMenuScreen" in source, (
            "Expected on_mount to reference MainMenuScreen"
        )


class TestMainMenuScreen:
    """Tests for the MainMenuScreen."""

    def _get_list_items_from_screen(self, screen):
        """Recursively collect all ListItem widgets from a Screen's compose tree."""
        from textual.widgets import ListItem

        items = []
        for w in list(screen.compose()):
            if isinstance(w, ListItem):
                items.append(w)
            # Recurse into container children and pending children
            for child in list(getattr(w, "children", [])):
                if isinstance(child, ListItem):
                    items.append(child)
            for child in list(getattr(w, "_pending_children", [])):
                if isinstance(child, ListItem):
                    items.append(child)
        return items

    def test_main_menu_has_three_items(self) -> None:
        """MainMenuScreen compose method yields 3 ListItems."""
        screen = MainMenuScreen()
        list_items = self._get_list_items_from_screen(screen)
        assert len(list_items) == 3, (
            f"Expected 3 ListItems, got {len(list_items)}"
        )

    def test_main_menu_has_correct_item_labels(self) -> None:
        """MainMenuScreen ListItems contain expected labels."""
        screen = MainMenuScreen()
        from textual.widgets import Static
        labels = []
        for item in self._get_list_items_from_screen(screen):
            # Each ListItem contains a Static with the label text in pending children
            for child in list(getattr(item, "_pending_children", [])):
                if isinstance(child, Static):
                    # The text content is stored in the name-mangled attribute
                    content = getattr(child, "_Static__content", None)
                    if content:
                        labels.append(content)
        assert "Search" in labels, f"Expected 'Search' in labels, got {labels}"
        assert "Settings" in labels, f"Expected 'Settings' in labels, got {labels}"
        assert "Quit" in labels, f"Expected 'Quit' in labels, got {labels}"

    def test_main_menu_has_bindings(self) -> None:
        """MainMenuScreen has enter binding for select."""
        screen = MainMenuScreen()
        # Screen BINDINGS is a list of (key, action, description) tuples
        bindings = {b[0]: b[1] for b in screen.BINDINGS}
        assert "enter" in bindings, "Expected 'enter' key binding"
        assert bindings["enter"] == "select"
