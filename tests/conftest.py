"""Shared pytest fixtures.

Resets the shared rate limiter before/after every test so one test's
calls to /api/assist don't eat into another test's rate-limit budget.
"""

from __future__ import annotations

import logging
import os

import pytest

from app.core.context_engine import OVERRIDES_FILE, _live_turnstile_overrides
from app.core.limiter import limiter

_log = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def _reset_test_state():
    # Reset rate limiter
    limiter.reset()
    # Reset JSON overrides database file
    if os.path.exists(OVERRIDES_FILE):
        try:
            os.remove(OVERRIDES_FILE)
        except OSError as exc:
            _log.warning("Could not remove overrides file: %s", exc)
    _live_turnstile_overrides.clear()

    yield

    limiter.reset()
    if os.path.exists(OVERRIDES_FILE):
        try:
            os.remove(OVERRIDES_FILE)
        except OSError as exc:
            _log.warning("Could not remove overrides file on teardown: %s", exc)
    _live_turnstile_overrides.clear()
