"""Unit tests for the firestore_client module.

Verifies that:
1. When GOOGLE_CLOUD_PROJECT is not set, get_client() returns None (local mode).
2. When GOOGLE_CLOUD_PROJECT is set, it attempts to load firestore.Client.
3. Operations like fetch_venue_config and fetch_all_overrides fall back gracefully.
"""

from __future__ import annotations

import os
import sys
from unittest.mock import MagicMock, patch

# Inject a mock google.cloud.firestore module into sys.modules to prevent
# ModuleNotFoundError in environments without google-cloud-firestore installed
mock_firestore = MagicMock()
mock_client_instance = MagicMock()
mock_firestore.Client.return_value = mock_client_instance

mock_google_cloud = MagicMock()
mock_google_cloud.firestore = mock_firestore

sys.modules["google"] = MagicMock()
sys.modules["google.cloud"] = mock_google_cloud
sys.modules["google.cloud.firestore"] = mock_firestore

from app.core import firestore_client  # noqa: E402


def test_firestore_client_local_mode():
    """Verify that get_client() returns None when GOOGLE_CLOUD_PROJECT is not set."""
    firestore_client._initialised = False
    firestore_client._client = None

    with patch.dict(os.environ, {}, clear=True):
        client = firestore_client.get_client()
        assert client is None


def test_firestore_client_gcp_mode():
    """Verify that get_client() attempts to initialize Firestore when project is set."""
    firestore_client._initialised = False
    firestore_client._client = None

    with patch.dict(os.environ, {"GOOGLE_CLOUD_PROJECT": "test-project"}):
        client = firestore_client.get_client()
        assert client == mock_client_instance


def test_fetch_venue_config_fallback():
    """Verify that fetch_venue_config returns None when in local mode."""
    firestore_client._initialised = False
    firestore_client._client = None

    with patch.dict(os.environ, {}, clear=True):
        config = firestore_client.fetch_venue_config()
        assert config is None


def test_fetch_all_overrides_fallback():
    """Verify that fetch_all_overrides returns {} when in local mode."""
    firestore_client._initialised = False
    firestore_client._client = None

    with patch.dict(os.environ, {}, clear=True):
        overrides = firestore_client.fetch_all_overrides()
        assert overrides == {}
