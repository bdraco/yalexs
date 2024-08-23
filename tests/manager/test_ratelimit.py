from yalexs.manager.ratelimit import _RateLimitChecker

import pytest
from yalexs.exceptions import RateLimited


@pytest.mark.asyncio
async def test_init_rate_limit():
    _RateLimitChecker._client_wakeups.clear()

    await _RateLimitChecker.check_rate_limit("test")
    await _RateLimitChecker.register_wakeup("test")
    with pytest.raises(RateLimited):
        await _RateLimitChecker.check_rate_limit("test")
