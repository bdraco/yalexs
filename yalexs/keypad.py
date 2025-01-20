from ._compat import cached_property
from .device import DeviceDetail

BATTERY_LEVEL_FULL = "Full"
BATTERY_LEVEL_MEDIUM = "Medium"
BATTERY_LEVEL_LOW = "Low"

_LEVEL_TO_VALUE = {
    BATTERY_LEVEL_FULL: 100,
    BATTERY_LEVEL_MEDIUM: 60,
    BATTERY_LEVEL_LOW: 10,
}

_MAX_LEVEL = 200
_MIN_LEVEL = 120
_RATIO = 100 / (_MAX_LEVEL - _MIN_LEVEL)


class KeypadDetail(DeviceDetail):
    def __init__(self, house_id, keypad_name, data):
        super().__init__(
            data["_id"],
            keypad_name,
            house_id,
            data["serialNumber"],
            data["currentFirmwareVersion"],
            None,
            data,
        )
        self._battery_raw = data.get("batteryRaw")
        self._battery_level = data["batteryLevel"]

    @cached_property
    def model(self):
        return "AK-R1"

    @cached_property
    def battery_level(self):
        return self._battery_level

    @cached_property
    def battery_percentage(self):
        """Return an approximation of the battery percentage."""
        if self._battery_raw is not None:
            return int(max(0, min(100, (self._battery_raw - _MIN_LEVEL) * _RATIO)))
        if self._battery_level is None:
            return None
        return _LEVEL_TO_VALUE.get(self._battery_level, 0)
