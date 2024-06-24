"""Constants."""

from __future__ import annotations

from datetime import timedelta
from typing import Final

DEFAULT_TIMEOUT = 25

CONF_USERNAME: Final = "username"
CONF_PASSWORD: Final = "password"
CONF_TIMEOUT: Final = "timeout"
CONF_ACCESS_TOKEN_CACHE_FILE: Final = "access_token_cache_file"
CONF_BRAND: Final = "brand"
CONF_LOGIN_METHOD: Final = "login_method"
CONF_INSTALL_ID: Final = "install_id"
VERIFICATION_CODE_KEY: Final = "verification_code"

DEFAULT_AUGUST_CONFIG_FILE: Final = ".august.conf"

# Activity needs to be checked more frequently as the
# doorbell motion and rings are included here
ACTIVITY_UPDATE_INTERVAL = timedelta(seconds=10)


# Limit battery, online, and hardware updates to hourly
# in order to reduce the number of api requests and
# avoid hitting rate limits
MIN_TIME_BETWEEN_DETAIL_UPDATES = timedelta(hours=24)
