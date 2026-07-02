"""Shared fixtures for cache tests."""

import pytest
from gitrank.cache.db import CacheDB


@pytest.fixture
def temp_db():
    """Create an in-memory CacheDB, initialize it, yield it, close after test."""
    db = CacheDB(db_path=":memory:")
    db.initialize()
    yield db
    db.close()
