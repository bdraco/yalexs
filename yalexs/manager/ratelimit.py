"""Support for August devices."""

from __future__ import annotations

from ..exceptions import RateLimited
from collections import defaultdict
import time

RATE_LIMIT_WAKEUP_INTERVAL = 60 * 26

_NEVER_TIME = -RATE_LIMIT_WAKEUP_INTERVAL


class RateLimitCheck:
    """The rate limit is checked locally here to avoid getting blocked.

    This is a basic rate limit checker that will check the rate limit
    locally to avoid getting blocked.

    If rate limiting is not checked locally there is a risk that the
    client will get permanently blocked by the server.
    """

    def __init__(self) -> None:
        """Initialize the rate limit checker."""
        self._client_wakeups: defaultdict[str, float] = defaultdict(lambda: _NEVER_TIME)

    async def check_rate_limit(self, token: str) -> None:
        """Check if the client is rate limited."""
        now = time.monotonic()
        next_allowed = now - (self._client_wakeups[token] + RATE_LIMIT_WAKEUP_INTERVAL)
        if next_allowed < now:
            min_next_allowed = int((now - next_allowed) / 60)
            raise RateLimited(f"Rate limited, try again in {min_next_allowed} minutes")

    async def register_wakeup(self, token: str) -> None:
        """Register a wakeup for the client."""
        self._client_wakeups[token] = time.monotonic()


_RateLimitChecker = RateLimitCheck()