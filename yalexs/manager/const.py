"""Constants for August devices."""
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

NOTIFICATION_ID = "august_notification"
NOTIFICATION_TITLE = "August"

MANUFACTURER = "August Home Inc."

DEFAULT_AUGUST_CONFIG_FILE: Final = ".august.conf"

DEFAULT_NAME = "August"
DOMAIN = "august"

OPERATION_METHOD_AUTORELOCK = "autorelock"
OPERATION_METHOD_REMOTE = "remote"
OPERATION_METHOD_KEYPAD = "keypad"
OPERATION_METHOD_MANUAL = "manual"
OPERATION_METHOD_TAG = "tag"
OPERATION_METHOD_MOBILE_DEVICE = "mobile"

ATTR_OPERATION_AUTORELOCK = "autorelock"
ATTR_OPERATION_METHOD = "method"
ATTR_OPERATION_REMOTE = "remote"
ATTR_OPERATION_KEYPAD = "keypad"
ATTR_OPERATION_MANUAL = "manual"
ATTR_OPERATION_TAG = "tag"

# Limit battery, online, and hardware updates to hourly
# in order to reduce the number of api requests and
# avoid hitting rate limits
MIN_TIME_BETWEEN_DETAIL_UPDATES = timedelta(hours=24)

# Activity needs to be checked more frequently as the
# doorbell motion and rings are included here
ACTIVITY_UPDATE_INTERVAL = timedelta(seconds=10)

LOGIN_METHODS = ["phone", "email"]
DEFAULT_LOGIN_METHOD = "email"
