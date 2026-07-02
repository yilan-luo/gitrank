"""TUI state management for the search wizard."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SearchState:
    """Tracks wizard search parameters across screens."""

    topic: str = ""
    time_window: str = "all"  # "all", "last_month", "last_3_months", "last_year", "custom"
    custom_since: Optional[str] = None  # ISO date string
    custom_until: Optional[str] = None  # ISO date string
    sort: str = "stars"  # "stars" or "composite"
