from __future__ import annotations

"""Shared constants for TUI screens.

Centralises option lists used by both the search wizard and settings
sub-pickers so that topic, time-window, and sort choices stay in sync.
"""

PRESET_TOPICS: list[str] = [
    "ai",
    "machine-learning",
    "web",
    "mobile",
    "devops",
    "game",
    "rust",
    "python",
    "javascript",
    "golang",
    "data-science",
    "security",
]

PRESET_TIME_WINDOWS: list[str] = [
    "all",
    "last_month",
    "last_3_months",
    "last_year",
    "custom",
]

SORT_OPTIONS: list[str] = [
    "stars",
    "composite",
]

TIME_WINDOW_LABELS: dict[str, str] = {
    "all": "All Time",
    "last_month": "Last Month",
    "last_3_months": "Last 3 Months",
    "last_year": "Last Year",
    "custom": "Custom",
}

SORT_LABELS: dict[str, str] = {
    "stars": "Stars",
    "composite": "Composite",
}
