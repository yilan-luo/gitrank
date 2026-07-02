"""Test TUI search wizard screens: topic, time, sort, and navigation bindings."""

import pytest

from gitrank.tui.screens.search_topic import SearchTopicScreen
from gitrank.tui.screens.search_time import SearchTimeScreen
from gitrank.tui.screens.search_sort import SearchSortScreen


def _collect_list_items(screen):
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


def _collect_inputs(screen):
    """Collect all Input widgets from a Screen's compose tree."""
    from textual.widgets import Input

    inputs = []
    for w in list(screen.compose()):
        if isinstance(w, Input):
            inputs.append(w)
    return inputs


def _list_item_labels(items):
    """Extract readable labels from ListItem widgets."""
    from textual.widgets import Static

    labels = []
    for item in items:
        for child in list(getattr(item, "_pending_children", [])):
            if isinstance(child, Static):
                content = getattr(child, "_Static__content", None)
                if content:
                    labels.append(str(content))
    return labels



class TestSearchTopicScreen:
    """Tests for the SearchTopicScreen."""

    def test_search_topic_has_preset_list(self) -> None:
        """SearchTopicScreen has a ListView with preset topic items."""
        screen = SearchTopicScreen()
        items = _collect_list_items(screen)
        labels = _list_item_labels(items)

        expected_topics = [
            "ai", "machine-learning", "web", "mobile", "devops",
            "game", "rust", "python", "javascript", "golang",
            "data-science", "security",
        ]
        for topic in expected_topics:
            assert topic in labels, (
                f"Expected '{topic}' in topic labels, got {labels}"
            )
        assert len(items) >= 12, (
            f"Expected at least 12 ListItems, got {len(items)}"
        )

    def test_search_topic_has_custom_input(self) -> None:
        """SearchTopicScreen has an Input widget for custom topic entry."""
        screen = SearchTopicScreen()
        inputs = _collect_inputs(screen)
        assert len(inputs) >= 1, (
            f"Expected at least 1 Input widget, got {len(inputs)}"
        )


class TestSearchTimeScreen:
    """Tests for the SearchTimeScreen."""

    def test_search_time_has_options(self) -> None:
        """SearchTimeScreen has a ListView with time window options."""
        screen = SearchTimeScreen()
        items = _collect_list_items(screen)
        labels = _list_item_labels(items)

        expected_options = ["All Time", "Last Month", "Last 3 Months", "Last Year", "Custom"]
        for option in expected_options:
            assert option in labels, (
                f"Expected '{option}' in time options, got {labels}"
            )
        assert len(items) >= 5, (
            f"Expected at least 5 ListItems, got {len(items)}"
        )

    def test_search_time_has_custom_date_inputs(self) -> None:
        """SearchTimeScreen includes Input widgets for custom date range."""
        screen = SearchTimeScreen()
        inputs = _collect_inputs(screen)
        assert len(inputs) >= 2, (
            f"Expected at least 2 Input widgets (since/until dates), got {len(inputs)}"
        )


class TestSearchSortScreen:
    """Tests for the SearchSortScreen."""

    def test_search_sort_has_options(self) -> None:
        """SearchSortScreen has Stars and Composite sort options."""
        screen = SearchSortScreen()
        items = _collect_list_items(screen)
        labels = _list_item_labels(items)

        assert len(items) >= 2, (
            f"Expected at least 2 ListItems, got {len(items)}"
        )
        assert "Stars" in labels, (
            f"Expected 'Stars' in sort options, got {labels}"
        )
        assert "Composite" in labels, (
            f"Expected 'Composite' in sort options, got {labels}"
        )


def _get_binding_map(screen):
    """Build a key->action map from screen BINDINGS.

    Handles both tuple format (older Textual) and Binding objects (Textual >= 2.0).
    """
    bindings = {}
    for b in screen.BINDINGS:
        if hasattr(b, "key"):
            bindings[b.key] = b.action
        else:
            bindings[b[0]] = b[1]
    return bindings


class TestScreenNavigationBindings:
    """Tests for navigation bindings on all search wizard screens."""

    @pytest.mark.parametrize("screen_cls, screen_name", [
        (SearchTopicScreen, "SearchTopicScreen"),
        (SearchTimeScreen, "SearchTimeScreen"),
        (SearchSortScreen, "SearchSortScreen"),
    ])
    def test_screen_has_navigation_bindings(self, screen_cls, screen_name) -> None:
        """Each search screen has Enter (select) and Escape (pop) bindings."""
        screen = screen_cls()
        bindings = _get_binding_map(screen)

        assert "enter" in bindings, (
            f"{screen_name}: expected 'enter' binding, got {list(bindings.keys())}"
        )
        assert "escape" in bindings, (
            f"{screen_name}: expected 'escape' binding, got {list(bindings.keys())}"
        )
