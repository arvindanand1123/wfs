"""Shared pytest fixtures."""

import pytest
from fastapi.testclient import TestClient

from wfs.main import create_app


@pytest.fixture
def client():
    """A test client wired to the app in-process (no network)."""
    return TestClient(create_app())
