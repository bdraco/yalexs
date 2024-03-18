"""Api functions common between sync and async."""

from __future__ import annotations

import datetime
import logging
from typing import Any

from .activity import ACTION_TO_CLASS, SOURCE_LOCK_OPERATE, SOURCE_LOG, ActivityTypes
from .const import BASE_URLS, BRANDING, Brand
from .doorbell import Doorbell
from .lock import Lock, LockDoorStatus, determine_door_state, door_state_to_string
from .time import parse_datetime

API_EXCEPTION_RETRY_TIME = 0.1
API_RETRY_TIME = 2.5
API_RETRY_ATTEMPTS = 10

HEADER_ACCEPT_VERSION = "Accept-Version"
HEADER_AUGUST_ACCESS_TOKEN = "x-august-access-token"  # nosec
HEADER_AUGUST_API_KEY = "x-august-api-key"
HEADER_AUGUST_BRANDING = "x-august-branding"
HEADER_AUGUST_COUNTRY = "x-august-country"
HEADER_CONTENT_TYPE = "Content-Type"
HEADER_USER_AGENT = "User-Agent"


HEADER_VALUE_API_KEY_OLD = "7cab4bbd-2693-4fc1-b99b-dec0fb20f9d4"
HEADER_VALUE_API_KEY = "d9984f29-07a6-816e-e1c9-44ec9d1be431"
HEADER_VALUE_CONTENT_TYPE = "application/json; charset=UTF-8"
HEADER_VALUE_USER_AGENT = "August/Luna-22.17.0 (Android; SDK 31; gphone64_arm64)"
HEADER_VALUE_ACCEPT_VERSION = "0.0.1"
HEADER_VALUE_AUGUST_BRANDING = "august"
HEADER_VALUE_AUGUST_COUNTRY = "US"


API_GET_SESSION_URL = "/session"
API_SEND_VERIFICATION_CODE_URLS = {
    "phone": "/validation/phone",
    "email": "/validation/email",
}
API_VALIDATE_VERIFICATION_CODE_URLS = {
    "phone": "/validate/phone",
    "email": "/validate/email",
}
API_GET_HOUSE_ACTIVITIES_URL = "/houses/{house_id}/activities"
API_GET_DOORBELLS_URL = "/users/doorbells/mine"
API_GET_DOORBELL_URL = "/doorbells/{doorbell_id}"
API_WAKEUP_DOORBELL_URL = "/doorbells/{doorbell_id}/wakeup"
API_GET_HOUSES_URL = "/users/houses/mine"
API_GET_HOUSE_URL = "/houses/{house_id}"
API_GET_LOCKS_URL = "/users/locks/mine"
API_GET_LOCK_URL = "/locks/{lock_id}"
API_GET_LOCK_STATUS_URL = "/locks/{lock_id}/status"
API_GET_PINS_URL = "/locks/{lock_id}/pins"
API_LOCK_URL = "/remoteoperate/{lock_id}/lock"
API_UNLOCK_URL = "/remoteoperate/{lock_id}/unlock"
API_UNLATCH_URL = "/remoteoperate/{lock_id}/unlatch"
API_LOCK_ASYNC_URL = "/remoteoperate/{lock_id}/lock?v=2.3.1&type=async"
API_UNLOCK_ASYNC_URL = "/remoteoperate/{lock_id}/unlock?v=2.3.1&type=async"
API_UNLATCH_ASYNC_URL = "/remoteoperate/{lock_id}/unlatch?v=2.3.1&type=async"
API_STATUS_ASYNC_URL = (
    "/remoteoperate/{lock_id}/status?v=2.3.1&type=async&intent=wakeup"
)
HYPER_BRIDGE_PARAM = "&connection=persistent"
API_GET_USER_URL = "/users/me"

_LOGGER = logging.getLogger(__name__)


def _api_headers(
    access_token: str | None = None, brand: Brand | None = None
) -> dict[str, str]:
    headers = {
        HEADER_ACCEPT_VERSION: HEADER_VALUE_ACCEPT_VERSION,
        HEADER_AUGUST_API_KEY: HEADER_VALUE_API_KEY,
        HEADER_CONTENT_TYPE: HEADER_VALUE_CONTENT_TYPE,
        HEADER_USER_AGENT: HEADER_VALUE_USER_AGENT,
        HEADER_AUGUST_COUNTRY: HEADER_VALUE_AUGUST_COUNTRY,
    }

    headers[HEADER_AUGUST_BRANDING] = BRANDING.get(brand, HEADER_VALUE_AUGUST_BRANDING)

    if access_token:
        headers[HEADER_AUGUST_ACCESS_TOKEN] = access_token

    return headers


def _convert_lock_result_to_activities(
    lock_json_dict: dict[str, Any]
) -> list[ActivityTypes]:
    activities = []
    lock_info_json_dict = lock_json_dict.get("info", {})
    lock_id = lock_info_json_dict.get("lockID")
    lock_action_text = lock_info_json_dict.get("action")
    activity_epoch = _datetime_string_to_epoch(lock_info_json_dict.get("startTime"))
    activity_lock_dict = _map_lock_result_to_activity(
        lock_id, activity_epoch, lock_action_text
    )
    activities.append(activity_lock_dict)

    door_state = determine_door_state(lock_json_dict.get("doorState"))
    if door_state not in (LockDoorStatus.UNKNOWN, LockDoorStatus.DISABLED):
        activity_door_dict = _map_lock_result_to_activity(
            lock_id, activity_epoch, door_state_to_string(door_state)
        )
        activities.append(activity_door_dict)

    return activities


def _activity_from_dict(
    source: str, activity_dict: dict[str, Any], debug: bool = False
) -> ActivityTypes | None:
    """Convert an activity dict to and Activity object."""
    if debug:
        _LOGGER.debug("Processing activity: %s", activity_dict)
    if (action := activity_dict.get("action")) and (
        klass := ACTION_TO_CLASS.get(action)
    ):
        return klass(source, activity_dict)
    if debug:
        _LOGGER.debug("Unknown activity: %s", activity_dict)
    return None


def _map_lock_result_to_activity(
    lock_id: str, activity_epoch: float, action_text: str
) -> ActivityTypes | None:
    """Create an yale access activity from a lock result."""
    mapped_dict = {
        "dateTime": activity_epoch,
        "deviceID": lock_id,
        "deviceType": "lock",
        "action": action_text,
    }
    return _activity_from_dict(
        SOURCE_LOCK_OPERATE, mapped_dict, _LOGGER.isEnabledFor(logging.DEBUG)
    )


def _datetime_string_to_epoch(datetime_string: str) -> datetime.datetime:
    return parse_datetime(datetime_string).timestamp() * 1000


def _process_activity_json(json_dict: dict[str, Any]) -> list[ActivityTypes]:
    if "events" in json_dict:
        json_dict = json_dict["events"]
    debug = _LOGGER.isEnabledFor(logging.DEBUG)
    activities: list[ActivityTypes] = []
    for activity_json in json_dict:
        if activity := _activity_from_dict(SOURCE_LOG, activity_json, debug):
            activities.append(activity)
    return activities


def _process_doorbells_json(json_dict: dict[str, Any]) -> list[Doorbell]:
    return [Doorbell(device_id, data) for device_id, data in json_dict.items()]


def _process_locks_json(json_dict: dict[str, Any]) -> list[Lock]:
    return [Lock(device_id, data) for device_id, data in json_dict.items()]


class ApiCommon:
    """Api dict shared between async and sync."""

    def __init__(self, brand: Brand) -> None:
        """Init."""
        self._base_url = BASE_URLS[brand]
        self.brand = brand

    def get_brand_url(self, url_str: str) -> str:
        """Get url."""
        return self._base_url + url_str

    def _build_get_session_request(self, install_id, identifier, password):
        return {
            "method": "post",
            "url": self.get_brand_url(API_GET_SESSION_URL),
            "json": {
                "installId": install_id,
                "identifier": identifier,
                "password": password,
            },
        }

    def _build_send_verification_code_request(
        self, access_token, login_method, username
    ):
        if login_method == "phone":
            json = {"smsHashString": "anY0ZsRmXw+", "value": username}
        else:
            json = {"value": username}

        return {
            "method": "post",
            "url": self.get_brand_url(API_SEND_VERIFICATION_CODE_URLS[login_method]),
            "access_token": access_token,
            "json": json,
        }

    def _build_validate_verification_code_request(
        self, access_token, login_method, username, verification_code
    ):
        return {
            "method": "post",
            "url": self.get_brand_url(
                API_VALIDATE_VERIFICATION_CODE_URLS[login_method]
            ),
            "access_token": access_token,
            "json": {login_method: username, "code": str(verification_code)},
        }

    def _build_get_doorbells_request(self, access_token):
        return {
            "method": "get",
            "url": self.get_brand_url(API_GET_DOORBELLS_URL),
            "access_token": access_token,
        }

    def _build_get_doorbell_detail_request(self, access_token, doorbell_id):
        return {
            "method": "get",
            "url": self.get_brand_url(
                API_GET_DOORBELL_URL.format(doorbell_id=doorbell_id)
            ),
            "access_token": access_token,
        }

    def _build_wakeup_doorbell_request(self, access_token, doorbell_id):
        return {
            "method": "put",
            "url": self.get_brand_url(
                API_WAKEUP_DOORBELL_URL.format(doorbell_id=doorbell_id)
            ),
            "access_token": access_token,
        }

    def _build_get_houses_request(self, access_token):
        return {"method": "get", "access_token": access_token}

    def _build_get_house_request(self, access_token, house_id):
        return {
            "method": "get",
            "url": self.get_brand_url(API_GET_HOUSE_URL.format(house_id=house_id)),
            "access_token": access_token,
        }

    def _build_get_house_activities_request(self, access_token, house_id, limit=8):
        return {
            "method": "get",
            "url": self.get_brand_url(
                API_GET_HOUSE_ACTIVITIES_URL.format(house_id=house_id)
            ),
            "version": "4.0.0",
            "access_token": access_token,
            "params": {"limit": limit},
        }

    def _build_get_locks_request(self, access_token):
        return {
            "method": "get",
            "url": self.get_brand_url(API_GET_LOCKS_URL),
            "access_token": access_token,
        }

    def _build_get_user_request(self, access_token):
        return {
            "method": "get",
            "url": self.get_brand_url(API_GET_USER_URL),
            "access_token": access_token,
        }

    def _build_get_lock_detail_request(self, access_token, lock_id):
        return {
            "method": "get",
            "url": self.get_brand_url(API_GET_LOCK_URL.format(lock_id=lock_id)),
            "access_token": access_token,
        }

    def _build_get_lock_status_request(self, access_token, lock_id):
        return {
            "method": "get",
            "url": self.get_brand_url(API_GET_LOCK_STATUS_URL.format(lock_id=lock_id)),
            "access_token": access_token,
        }

    def _build_get_pins_request(self, access_token, lock_id):
        return {
            "method": "get",
            "url": self.get_brand_url(API_GET_PINS_URL.format(lock_id=lock_id)),
            "access_token": access_token,
        }

    def _build_refresh_access_token_request(self, access_token):
        return {
            "method": "get",
            "url": self.get_brand_url(API_GET_HOUSES_URL),
            "access_token": access_token,
        }

    def _build_call_lock_operation_request(
        self, url_str: str, access_token: str, lock_id: str, timeout
    ) -> dict[str, Any]:
        return {
            "method": "put",
            "url": self.get_brand_url(url_str.format(lock_id=lock_id)),
            "access_token": access_token,
            "timeout": timeout,
        }
