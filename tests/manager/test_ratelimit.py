from yalexs.manager.ratelimit import _RateLimitChecker, RATE_LIMIT_WAKEUP_INTERVAL

import pytest
from yalexs.exceptions import RateLimited
import time


@pytest.mark.asyncio
async def test_init_rate_limit():
    _RateLimitChecker._client_wakeups.clear()

    await _RateLimitChecker.check_rate_limit("test")
    await _RateLimitChecker.register_wakeup("test")
    with pytest.raises(RateLimited) as exc:
        await _RateLimitChecker.check_rate_limit("test")

    assert exc.value.next_allowed == pytest.approx(
        time.monotonic() + RATE_LIMIT_WAKEUP_INTERVAL
    )
