from __future__ import annotations

from typing import Any

from .backports.functools import cached_property


class Device:
    """Base class for all devices."""

    def __init__(self, device_id: str, device_name: str, house_id: str) -> None:
        self._device_id = device_id
        self._device_name = device_name
        self._house_id = house_id

    @cached_property
    def device_id(self) -> str:
        return self._device_id

    @cached_property
    def device_name(self) -> str:
        return self._device_name

    @cached_property
    def house_id(self) -> str:
        return self._house_id


class DeviceDetail:
    def __init__(
        self,
        device_id: str,
        device_name: str,
        house_id: str,
        serial_number: str,
        firmware_version: str,
        pubsub_channel: str,
        data: dict[str, Any],
    ) -> None:
        self._device_id = device_id
        self._device_name = device_name
        self._house_id = house_id
        self._serial_number = serial_number
        self._firmware_version = firmware_version
        self._pubsub_channel = pubsub_channel
        self._data = data

    @cached_property
    def raw(self):
        return self._data

    @cached_property
    def device_id(self):
        return self._device_id

    @cached_property
    def device_name(self):
        return self._device_name

    @cached_property
    def house_id(self):
        return self._house_id

    @cached_property
    def serial_number(self):
        return self._serial_number

    @cached_property
    def firmware_version(self):
        return self._firmware_version

    @cached_property
    def pubsub_channel(self):
        return self._pubsub_channel
