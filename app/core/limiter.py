"""Single shared rate limiter instance.

Previously app/main.py and app/api/routes.py each created their own
Limiter() — two independent in-memory counters that never talked to
each other. Importing one instance from here fixes that.
"""
from __future__ import annotations

import os

from slowapi import Limiter
from slowapi.util import get_remote_address

redis_url = os.environ.get("REDIS_URL")
if redis_url:
    # Use Redis backed store for horizontal scaling
    limiter = Limiter(key_func=get_remote_address, storage_uri=redis_url)
else:
    # Fall back to in-memory store for development/testing
    limiter = Limiter(key_func=get_remote_address)

