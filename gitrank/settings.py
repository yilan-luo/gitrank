"""Settings manager for the GitHub Rank TUI application.

Reads and writes configuration to ``~/.gitrank/config.json``, merging with
sensible defaults for any missing keys.
"""

import json
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

DEFAULT_CONFIG = {
    "topic": "",
    "time_window": "last_6_months",
    "sort": "stars",
    "limit": 20,
}


@dataclass
class Settings:
    """Persistent user configuration backed by a JSON file.

    Attributes:
        config_dir: Directory where ``config.json`` is stored.
        config_file: Path to the JSON config file (derived from *config_dir*).
        data: In-memory copy of the loaded configuration dict.
    """

    config_dir: Path = field(default_factory=lambda: Path.home() / ".gitrank")
    config_file: Optional[Path] = None
    data: Optional[dict] = None

    def __post_init__(self) -> None:
        """Derive *config_file* from *config_dir* if not explicitly provided."""
        if self.config_file is None:
            self.config_file = self.config_dir / "config.json"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self) -> dict:
        """Load configuration from ``config.json``, merging with defaults.

        The config directory is created if it does not exist.  Any keys
        present in *DEFAULT_CONFIG* but missing from the file are filled
        in with the default values.

        Returns:
            The merged configuration dict (a copy, safe to mutate).
        """
        self.config_dir.mkdir(parents=True, exist_ok=True)

        merged = deepcopy(DEFAULT_CONFIG)

        if self.config_file.exists():
            try:
                raw = json.loads(self.config_file.read_text(encoding="utf-8"))
                merged.update(raw)
            except (json.JSONDecodeError, OSError):
                # If the file is corrupt, fall back to defaults.
                pass

        self.data = deepcopy(merged)
        return deepcopy(merged)

    def save(self, updates: dict) -> None:
        """Merge *updates* into the current configuration and write to disk.

        If no config has been loaded yet, defaults are loaded first.

        Args:
            updates: Key-value pairs to merge into the current config.
        """
        current = deepcopy(self.data) if self.data is not None else deepcopy(DEFAULT_CONFIG)
        current.update(updates)
        self.data = current

        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file.write_text(
            json.dumps(self.data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def update(self, key: str, value) -> None:
        """Update a single key and persist immediately.

        Args:
            key: Configuration key to update.
            value: New value for the key.
        """
        self.save({key: value})

    def get_defaults(self) -> dict:
        """Return a copy of the default configuration.

        Returns:
            A new dict containing *DEFAULT_CONFIG* values (safe to mutate).
        """
        return deepcopy(DEFAULT_CONFIG)
