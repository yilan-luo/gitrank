"""RepoDetailScreen - Full metadata view for a single repository."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer, Header, Static

from gitrank.api.models import RankedRepo


class RepoDetailScreen(Screen):
    """Shows full metadata and scores for a single ranked repository.

    Displays stars, forks, open issues, language, topics, dates,
    GitHub URL, and all computed scores.
    """

    BINDINGS = [
        ("escape", "pop_screen", "Back"),
    ]

    def __init__(self, repo: RankedRepo) -> None:
        super().__init__()
        self.ranked_repo = repo

    def compose(self) -> ComposeResult:
        r = self.ranked_repo.repo
        rr = self.ranked_repo

        yield Header()
        yield Static(f"Repository: {r.full_name}", id="detail_name")
        yield Static(
            f"Description: {r.description or 'N/A'}", id="detail_description"
        )
        yield Static(f"Language: {r.language or 'N/A'}", id="detail_language")
        yield Static(f"Stars: {r.stargazers_count}", id="detail_stars")
        yield Static(f"Forks: {r.forks_count}", id="detail_forks")
        yield Static(f"Open Issues: {r.open_issues_count}", id="detail_issues")
        yield Static(
            f"Topics: {', '.join(r.topics) if r.topics else 'N/A'}",
            id="detail_topics",
        )
        yield Static(
            f"Created: {r.created_at.strftime('%Y-%m-%d')}", id="detail_created"
        )
        yield Static(
            f"Updated: {r.updated_at.strftime('%Y-%m-%d')}", id="detail_updated"
        )
        yield Static(
            f"Last Push: {r.pushed_at.strftime('%Y-%m-%d')}", id="detail_pushed"
        )
        yield Static(f"GitHub URL: {r.html_url or 'N/A'}", id="detail_url")
        yield Static(f"Rank: #{rr.rank}", id="detail_rank")
        yield Static(f"Stars Score: {rr.stars_score:.3f}", id="detail_stars_score")
        yield Static(f"Growth Score: {rr.growth_score:.3f}", id="detail_growth_score")
        yield Static(
            f"Activity Score: {rr.activity_score:.3f}", id="detail_activity_score"
        )
        yield Static(
            f"Composite Score: {rr.composite_score:.3f}", id="detail_composite_score"
        )
        yield Static(
            f"Growth/Month: {rr.growth_per_month:.1f}", id="detail_growth_per_month"
        )
        yield Footer()
