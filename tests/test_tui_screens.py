"""Test TUI search wizard screens: topic, time, sort, and navigation bindings."""

from __future__ import annotations

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


# ---------------------------------------------------------------------------
# Helpers for Task 10 tests
# ---------------------------------------------------------------------------

def _make_test_ranked_repo(rank=1, full_name="test/repo", stars=100):
    """Create a minimal RankedRepo for testing."""
    from datetime import datetime, timezone

    from gitrank.api.models import RankedRepo, Repository

    repo = Repository(
        id=rank,
        full_name=full_name,
        description="A test repository",
        language="Python",
        topics=["testing", "example"],
        stargazers_count=stars,
        forks_count=10,
        open_issues_count=5,
        created_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2024, 6, 1, tzinfo=timezone.utc),
        pushed_at=datetime(2024, 6, 15, tzinfo=timezone.utc),
        html_url=f"https://github.com/{full_name}",
    )
    return RankedRepo(
        rank=rank,
        repo=repo,
        stars_score=0.8,
        growth_score=0.5,
        activity_score=0.6,
        composite_score=0.65,
        growth_per_month=10.5,
    )


# ---------------------------------------------------------------------------
# Task 10: LoadingScreen
# ---------------------------------------------------------------------------


class TestLoadingScreen:
    """Tests for the LoadingScreen."""

    def test_loading_screen_has_progress_bar(self) -> None:
        """LoadingScreen composes a ProgressBar widget."""
        from textual.widgets import ProgressBar

        from gitrank.tui.screens.loading import LoadingScreen

        screen = LoadingScreen()
        widgets = list(screen.compose())
        progress_bars = [w for w in widgets if isinstance(w, ProgressBar)]
        assert len(progress_bars) >= 1, (
            f"Expected at least 1 ProgressBar, got {len(progress_bars)}"
        )

    def test_loading_screen_has_status_text(self) -> None:
        """LoadingScreen composes a Static widget for status text."""
        from textual.widgets import Static

        from gitrank.tui.screens.loading import LoadingScreen

        screen = LoadingScreen()
        widgets = list(screen.compose())
        statics = [w for w in widgets if isinstance(w, Static)]
        assert len(statics) >= 1, (
            f"Expected at least 1 Static, got {len(statics)}"
        )


# ---------------------------------------------------------------------------
# Task 10: ResultsScreen
# ---------------------------------------------------------------------------


class TestResultsScreen:
    """Tests for the ResultsScreen."""

    def test_results_screen_has_datatable(self) -> None:
        """ResultsScreen composes a DataTable-based RepoTable widget."""
        from gitrank.tui.screens.results import ResultsScreen
        from gitrank.tui.widgets.repo_table import RepoTable

        screen = ResultsScreen([])
        widgets = list(screen.compose())
        tables = [w for w in widgets if isinstance(w, RepoTable)]
        assert len(tables) >= 1, (
            f"Expected at least 1 RepoTable, got {len(tables)}"
        )

    def test_results_screen_has_escape_binding(self) -> None:
        """ResultsScreen has an Escape key binding."""
        from gitrank.tui.screens.results import ResultsScreen

        screen = ResultsScreen([])
        bindings = _get_binding_map(screen)
        assert "escape" in bindings, (
            f"Expected 'escape' binding, got {list(bindings.keys())}"
        )


# ---------------------------------------------------------------------------
# Task 10: RepoTable
# ---------------------------------------------------------------------------


class TestRepoTable:
    """Tests for the RepoTable widget."""

    async def test_repo_table_populates_rows(self) -> None:
        """RepoTable.populate() fills the table with ranked repo rows."""
        from textual.app import App

        from gitrank.tui.widgets.repo_table import RepoTable

        ranked = _make_test_ranked_repo(rank=1, full_name="test/repo", stars=100)

        class _TestApp(App):
            """Minimal app to provide an active context for DataTable."""

            def compose(self) -> ComposeResult:
                yield RepoTable(id="table")

        app = _TestApp()
        async with app.run_test() as _pilot:
            table = app.query_one("#table", RepoTable)
            table.populate([ranked])
            assert table.row_count == 1, (
                f"Expected 1 row, got {table.row_count}"
            )


# ---------------------------------------------------------------------------
# Task 10: RepoDetailScreen
# ---------------------------------------------------------------------------


class TestRepoDetailScreen:
    """Tests for the RepoDetailScreen."""

    def test_repo_detail_displays_metadata(self) -> None:
        """RepoDetailScreen has Static labels for stars, language, and scores."""
        from textual.widgets import Static

        from gitrank.tui.widgets.repo_detail import RepoDetailScreen

        ranked = _make_test_ranked_repo(rank=1, full_name="test/repo", stars=100)
        screen = RepoDetailScreen(ranked)
        widgets = list(screen.compose())

        static_ids: set[str] = set()
        for w in widgets:
            if isinstance(w, Static):
                sid = getattr(w, "id", None)
                if sid:
                    static_ids.add(sid)

        expected_ids = {
            "detail_stars",
            "detail_language",
            "detail_stars_score",
            "detail_growth_score",
            "detail_activity_score",
            "detail_composite_score",
        }
        for eid in expected_ids:
            assert eid in static_ids, (
                f"Expected '{eid}' in static IDs, got {static_ids}"
            )
