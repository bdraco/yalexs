from __future__ import annotations

from datetime import datetime
from enum import Enum

import dateutil.parser

from yalexs.lock import LockDoorStatus, LockStatus
from yalexs.users import get_user_info

ACTION_LOCK_ONETOUCHLOCK = "onetouchlock"
ACTION_LOCK_ONETOUCHLOCK_2 = "one_touch_lock"
ACTION_LOCK_LOCK = "lock"
ACTION_RF_LOCK = "rf_lock"
ACTION_RF_SECURE = "rf_secure"
ACTION_RF_UNLOCK = "rf_unlock"
ACTION_LOCK_AUTO_LOCK = "auto_lock"
ACTION_LOCK_BLE_LOCK = "ble_lock"
ACTION_LOCK_BLE_UNLOCK = "ble_unlock"
ACTION_LOCK_REMOTE_LOCK = "remote_lock"
ACTION_LOCK_REMOTE_UNLOCK = "remote_unlock"
ACTION_LOCK_PIN_UNLOCK = "pin_unlock"
ACTION_LOCK_MANUAL_LOCK = "manual_lock"
ACTION_LOCK_MANUAL_UNLOCK = "manual_unlock"
ACTION_LOCK_LOCKING = "locking"
ACTION_LOCK_UNLOCK = "unlock"
ACTION_LOCK_UNLOCKING = "unlocking"
ACTION_LOCK_JAMMED = "jammed"

ACTION_DOOR_OPEN = "dooropen"
ACTION_DOOR_OPEN_2 = "door_open"
ACTION_DOOR_CLOSED = "doorclosed"
ACTION_DOOR_CLOSE_2 = "door_close"


ACTION_DOORBELL_CALL_INITIATED = "doorbell_call_initiated"
ACTION_DOORBELL_MOTION_DETECTED = "doorbell_motion_detected"
ACTION_DOORBELL_CALL_MISSED = "doorbell_call_missed"
ACTION_DOORBELL_CALL_HANGUP = "doorbell_call_hangup"

ACTION_BRIDGE_ONLINE = "associated_bridge_online"  # pubnub only
ACTION_BRIDGE_OFFLINE = "associated_bridge_offline"  # pubnub only
ACTION_DOORBELL_IMAGE_CAPTURE = "imagecapture"  # pubnub only
ACTION_DOORBELL_BUTTON_PUSHED = "buttonpush"  # pubnub only

ACTIVITY_ACTIONS_BRIDGE_OPERATION = {ACTION_BRIDGE_ONLINE, ACTION_BRIDGE_OFFLINE}

ACTIVITY_ACTIONS_DOORBELL_DING = {
    ACTION_DOORBELL_BUTTON_PUSHED,
    ACTION_DOORBELL_CALL_MISSED,
    ACTION_DOORBELL_CALL_HANGUP,
}
ACTIVITY_ACTIONS_DOORBELL_IMAGE_CAPTURE = {ACTION_DOORBELL_IMAGE_CAPTURE}
ACTIVITY_ACTIONS_DOORBELL_MOTION = {ACTION_DOORBELL_MOTION_DETECTED}
ACTIVITY_ACTIONS_DOORBELL_VIEW = {ACTION_DOORBELL_CALL_INITIATED}
ACTIVITY_ACTIONS_LOCK_OPERATION = {
    ACTION_RF_SECURE,
    ACTION_RF_LOCK,
    ACTION_RF_UNLOCK,
    ACTION_LOCK_AUTO_LOCK,
    ACTION_LOCK_ONETOUCHLOCK,
    ACTION_LOCK_ONETOUCHLOCK_2,
    ACTION_LOCK_LOCK,
    ACTION_LOCK_UNLOCK,
    ACTION_LOCK_LOCKING,
    ACTION_LOCK_UNLOCKING,
    ACTION_LOCK_JAMMED,
    ACTION_LOCK_BLE_LOCK,
    ACTION_LOCK_BLE_UNLOCK,
    ACTION_LOCK_REMOTE_LOCK,
    ACTION_LOCK_REMOTE_UNLOCK,
    ACTION_LOCK_PIN_UNLOCK,
    ACTION_LOCK_MANUAL_LOCK,
    ACTION_LOCK_MANUAL_UNLOCK,
}


ACTIVITY_TO_FIRST_LAST_NAME = {
    ACTION_RF_SECURE: ("Radio Frequency", "Secure"),
    ACTION_RF_LOCK: ("Radio Frequency", "Lock"),
    ACTION_RF_UNLOCK: ("Radio Frequency", "Unlock"),
    ACTION_LOCK_AUTO_LOCK: ("Auto", "Lock"),
    ACTION_LOCK_ONETOUCHLOCK: ("One-Touch", "Lock"),
    ACTION_LOCK_ONETOUCHLOCK_2: ("One-Touch", "Lock"),
    ACTION_LOCK_BLE_LOCK: ("Bluetooth", "Lock"),
    ACTION_LOCK_BLE_UNLOCK: ("Bluetooth", "Unlock"),
    ACTION_LOCK_MANUAL_LOCK: ("Manual", "Lock"),
    ACTION_LOCK_MANUAL_UNLOCK: ("Manual", "Unlock"),
}


ACTIVITY_ACTIONS_DOOR_OPERATION = {
    ACTION_DOOR_CLOSED,
    ACTION_DOOR_OPEN,
    ACTION_DOOR_OPEN_2,
    ACTION_DOOR_CLOSE_2,
}

KEYPAD_ACTIONS = {
    ACTION_LOCK_ONETOUCHLOCK,
    ACTION_LOCK_ONETOUCHLOCK_2,
    ACTION_LOCK_PIN_UNLOCK,
}
REMOTE_ACTIONS = {
    ACTION_LOCK_REMOTE_LOCK,
    ACTION_LOCK_REMOTE_UNLOCK,
}
AUTO_RELOCK_ACTIONS = {ACTION_LOCK_AUTO_LOCK}

ACTIVITY_ACTION_STATES = {
    ACTION_RF_SECURE: LockStatus.LOCKED,
    ACTION_RF_LOCK: LockStatus.LOCKED,
    ACTION_RF_UNLOCK: LockStatus.UNLOCKED,
    ACTION_LOCK_AUTO_LOCK: LockStatus.LOCKED,
    ACTION_LOCK_ONETOUCHLOCK: LockStatus.LOCKED,
    ACTION_LOCK_ONETOUCHLOCK_2: LockStatus.LOCKED,
    ACTION_LOCK_LOCK: LockStatus.LOCKED,
    ACTION_LOCK_UNLOCK: LockStatus.UNLOCKED,
    ACTION_LOCK_LOCKING: LockStatus.LOCKING,
    ACTION_LOCK_UNLOCKING: LockStatus.UNLOCKING,
    ACTION_LOCK_JAMMED: LockStatus.JAMMED,
    ACTION_DOOR_OPEN: LockDoorStatus.OPEN,
    ACTION_DOOR_CLOSED: LockDoorStatus.CLOSED,
    ACTION_DOOR_OPEN_2: LockDoorStatus.OPEN,
    ACTION_DOOR_CLOSE_2: LockDoorStatus.CLOSED,
    ACTION_LOCK_BLE_LOCK: LockStatus.LOCKED,
    ACTION_LOCK_BLE_UNLOCK: LockStatus.UNLOCKED,
    ACTION_LOCK_REMOTE_LOCK: LockStatus.LOCKED,
    ACTION_LOCK_REMOTE_UNLOCK: LockStatus.UNLOCKED,
    ACTION_LOCK_PIN_UNLOCK: LockStatus.UNLOCKED,
    ACTION_LOCK_MANUAL_LOCK: LockStatus.LOCKED,
    ACTION_LOCK_MANUAL_UNLOCK: LockStatus.UNLOCKED,
}

SOURCE_LOCK_OPERATE = "lock_operate"
SOURCE_PUBNUB = "pubnub"
SOURCE_LOG = "log"


def epoch_to_datetime(epoch: str | int | float) -> datetime:
    return datetime.fromtimestamp(float(epoch) / 1000.0)


class ActivityType(Enum):
    DOORBELL_MOTION = "doorbell_motion"
    DOORBELL_DING = "doorbell_ding"
    DOORBELL_VIEW = "doorbell_view"
    LOCK_OPERATION = "lock_operation"
    LOCK_OPERATION_WITHOUT_OPERATOR = "lock_operation_without_operator"
    DOOR_OPERATION = "door_operation"
    BRIDGE_OPERATION = "bridge_operation"
    DOORBELL_IMAGE_CAPTURE = "doorbell_image_capture"


class Activity:
    def __init__(self, source, activity_type, data):
        self._source = source
        self._activity_type = activity_type

        entities = data.get("entities", {})
        self._activity_id = entities.get("activity")
        self._house_id = entities.get("house")

        self._activity_time = epoch_to_datetime(
            data.get("dateTime", data.get("timestamp"))
        )
        self._action = data.get("action")
        self._device_id = data.get("deviceID")
        self._device_name = data.get("deviceName")
        self._device_type = data.get("deviceType")

    def __repr__(self):
        return (
            f"<{self.__class__.__name__} action={self.action} activity_type={self.activity_type} "
            f"activity_start_time={self.activity_start_time} "
            f"device_name={self.device_name}>"
        )

    @property
    def source(self):
        return self._source

    @property
    def activity_type(self):
        return self._activity_type

    @property
    def activity_id(self):
        return self._activity_id

    @property
    def house_id(self):
        return self._house_id

    @property
    def activity_start_time(self):
        return self._activity_time

    @property
    def activity_end_time(self):
        return self._activity_time

    @property
    def action(self):
        return self._action

    @property
    def device_id(self):
        return self._device_id

    @property
    def device_name(self):
        return self._device_name

    @property
    def device_type(self):
        return self._device_type


class BaseDoorbellMotionActivity(Activity):
    def __init__(self, source, activity_type, data):
        super().__init__(source, activity_type, data)
        image = data.get("info", {}).get("image")
        self._image_url = (
            None if image is None else image.get("secure_url")
        ) or data.get("attachment")
        self._image_created_at_datetime = None
        if image is None:
            return
        if "created_at" in image:
            self._image_created_at_datetime = dateutil.parser.parse(image["created_at"])
        else:
            self._image_created_at_datetime = self._activity_time

    def __repr__(self):
        return (
            f"<{self.__class__.__name__} action={self.action} activity_type={self.activity_type} "
            f"activity_start_time={self.activity_start_time} "
            f"device_name={self.device_name}"
            f"image_url={self.image_url}>"
        )

    @property
    def image_url(self):
        return self._image_url

    @property
    def image_created_at_datetime(self):
        return self._image_created_at_datetime


class DoorbellMotionActivity(BaseDoorbellMotionActivity):
    def __init__(self, source, data):
        super().__init__(source, ActivityType.DOORBELL_MOTION, data)


class DoorbellImageCaptureActivity(BaseDoorbellMotionActivity):
    """A motion activity with an image."""

    def __init__(self, source, data):
        super().__init__(source, ActivityType.DOORBELL_IMAGE_CAPTURE, data)


class DoorbellBaseActionActivity(Activity):
    def __init__(self, source, activity_type, data):
        super().__init__(source, activity_type, data)

        info = data.get("info", {})
        if "started" in info:
            self._activity_start_time = epoch_to_datetime(info["started"])
        else:
            self._activity_start_time = self._activity_time
        if "ended" in info:
            self._activity_end_time = epoch_to_datetime(info["ended"])
        else:
            self._activity_end_time = self._activity_time
        self._image_url = info.get("image") or info.get("attachment")

    @property
    def image_url(self):
        return self._image_url

    @property
    def activity_start_time(self):
        return self._activity_start_time

    @property
    def activity_end_time(self):
        return self._activity_end_time


class DoorbellDingActivity(DoorbellBaseActionActivity):
    def __init__(self, source, data):
        super().__init__(source, ActivityType.DOORBELL_DING, data)


class DoorbellViewActivity(DoorbellBaseActionActivity):
    def __init__(self, source, data):
        super().__init__(source, ActivityType.DOORBELL_VIEW, data)


class LockOperationActivity(Activity):
    def __init__(self, source, data):
        calling_user = data.get("callingUser", data.get("user", {}))
        action = data.get("action")
        info = data.get("info", {})
        user_id = calling_user.get("UserID")
        self._operated_remote = info.get("remote", action in REMOTE_ACTIONS)
        self._operated_keypad = info.get("keypad", action in KEYPAD_ACTIONS)
        self._operated_autorelock = (
            user_id == "automaticrelock" or action in AUTO_RELOCK_ACTIONS
        )
        first_name = calling_user.get("FirstName")
        last_name = calling_user.get("LastName")
        yale_user = get_user_info(user_id)
        if yale_user and first_name is None and last_name is None:
            first_name = yale_user.first_name
            last_name = yale_user.last_name

        # For legacy compatibility, we need to set the first_name and last_name
        # if its a physical or rf lock operation
        if (
            first_name is None
            and last_name is None
            and action in ACTIVITY_TO_FIRST_LAST_NAME
        ):
            first_name, last_name = ACTIVITY_TO_FIRST_LAST_NAME[action]

        if first_name is None and last_name is None:
            self._operated_by = None
            activity_type = ActivityType.LOCK_OPERATION_WITHOUT_OPERATOR
        else:
            self._operated_by = f"{first_name} {last_name}"
            activity_type = ActivityType.LOCK_OPERATION

        super().__init__(source, activity_type, data)

        image_info = calling_user.get("imageInfo") or calling_user
        original = image_info.get("original", {})
        if isinstance(original, str):
            self._operator_image_url = original
        elif isinstance(original, dict):
            self._operator_image_url = original.get("secure_url", None)
        else:
            self._operator_image_url = None

        thumbnail = image_info.get("thumbnail", {})
        if isinstance(thumbnail, str):
            self._operator_thumbnail_url = thumbnail
        elif isinstance(thumbnail, dict):
            self._operator_thumbnail_url = thumbnail.get("secure_url", None)
        else:
            self._operator_thumbnail_url = None

        if (
            yale_user
            and self._operator_image_url is None
            and self._operator_thumbnail_url is None
        ):
            self._operator_image_url = yale_user.image_url
            self._operator_thumbnail_url = yale_user.thumbnail_url

        if not self._operator_thumbnail_url:
            icon = data.get("icon")
            if icon:
                self._operator_thumbnail_url = icon

        if self._operator_image_url and not self._operator_thumbnail_url:
            self._operator_thumbnail_url = self._operator_image_url
        if self._operator_thumbnail_url and not self._operator_image_url:
            self._operator_image_url = self._operator_thumbnail_url

    def __repr__(self):
        return (
            f"<{self.__class__.__name__} action={self.action} activity_type={self.activity_type} "
            f"activity_start_time={self.activity_start_time} "
            f"device_name={self.device_name} "
            f"operated_by={self.operated_by} "
            f"operated_remote={self.operated_remote} "
            f"operated_keypad={self.operated_keypad} "
            f"operated_autorelock={self.operated_autorelock} "
            f"operator_image_url={self.operator_image_url} "
            f"operator_thumbnail_url={self.operator_thumbnail_url}>"
        )

    @property
    def operated_by(self):
        return self._operated_by

    @property
    def operated_remote(self):
        """Operation was remote."""
        return self._operated_remote

    @property
    def operated_keypad(self):
        """Operation used keypad."""
        return self._operated_keypad

    @property
    def operated_autorelock(self):
        """Operation done by automatic relock."""
        return self._operated_autorelock

    @property
    def operator_image_url(self):
        """URL to the image of the lock operator."""
        return self._operator_image_url

    @property
    def operator_thumbnail_url(self):
        """URL to the thumbnail of the lock operator."""
        return self._operator_thumbnail_url


class DoorOperationActivity(Activity):
    def __init__(self, source, data):
        super().__init__(source, ActivityType.DOOR_OPERATION, data)


class BridgeOperationActivity(Activity):
    def __init__(self, source, data):
        super().__init__(source, ActivityType.BRIDGE_OPERATION, data)
