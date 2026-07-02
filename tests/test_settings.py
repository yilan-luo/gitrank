"""Tests for gitrank.settings -- Settings manager."""

import json
import tempfile
from pathlib import Path

import pytest

from gitrank.settings import DEFAULT_CONFIG, Settings


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def temp_config_dir():
    """Create a temporary config directory, yield it, and clean up after."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


# ---------------------------------------------------------------------------
# 1. load() returns defaults when no config file exists
# ---------------------------------------------------------------------------


def test_load_returns_defaults_when_no_config_file(temp_config_dir):
    """load() returns the default configuration when config.json does not exist."""
    settings = Settings(config_dir=temp_config_dir)
    result = settings.load()

    assert result == DEFAULT_CONFIG
    # Keys from defaults should all be present
    for key in DEFAULT_CONFIG:
        assert key in result
        assert result[key] == DEFAULT_CONFIG[key]


# ---------------------------------------------------------------------------
# 2. save() writes config and load() reads it back
# ---------------------------------------------------------------------------


def test_save_writes_config_and_load_reads_back(temp_config_dir):
    """save() writes config to disk and load() returns the updated config."""
    settings = Settings(config_dir=temp_config_dir)

    updates = {"topic": "machine-learning", "limit": 50}
    settings.save(updates)

    # Verify file was created
    config_file = temp_config_dir / "config.json"
    assert config_file.exists()

    # Verify raw file content
    raw = json.loads(config_file.read_text(encoding="utf-8"))
    assert raw["topic"] == "machine-learning"
    assert raw["limit"] == 50
    # Unchanged keys should still be the defaults
    assert raw["time_window"] == DEFAULT_CONFIG["time_window"]
    assert raw["sort"] == DEFAULT_CONFIG["sort"]

    # Verify load() returns the merged config
    result = settings.load()
    assert result["topic"] == "machine-learning"
    assert result["limit"] == 50
    assert result["time_window"] == DEFAULT_CONFIG["time_window"]


# ---------------------------------------------------------------------------
# 3. update() changes a single key and saves
# ---------------------------------------------------------------------------


def test_update_changes_single_key(temp_config_dir):
    """update() changes a single setting key and persists it."""
    settings = Settings(config_dir=temp_config_dir)
    settings.load()  # initialise in-memory data

    settings.update("sort", "composite")

    # Verify file was written
    config_file = temp_config_dir / "config.json"
    assert config_file.exists()

    raw = json.loads(config_file.read_text(encoding="utf-8"))
    assert raw["sort"] == "composite"
    # Other keys should remain at defaults
    assert raw["topic"] == DEFAULT_CONFIG["topic"]

    # A new Settings instance with same dir should read the updated value
    settings2 = Settings(config_dir=temp_config_dir)
    result = settings2.load()
    assert result["sort"] == "composite"


# ---------------------------------------------------------------------------
# 4. get_defaults() returns default dict
# ---------------------------------------------------------------------------


def test_get_defaults_returns_default_dict(temp_config_dir):
    """get_defaults() returns a copy of the default configuration."""
    settings = Settings(config_dir=temp_config_dir)
    defaults = settings.get_defaults()

    assert defaults == DEFAULT_CONFIG
    assert defaults is not DEFAULT_CONFIG  # should be a copy, not the same object
    assert defaults["topic"] == "ai"
