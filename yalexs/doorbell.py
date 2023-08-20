from __future__ import annotations

import datetime
from typing import Any

from aiohttp import ClientSession
import requests

from .backports.functools import cached_property
from .device import Device, DeviceDetail
from .time import parse_datetime

DOORBELL_STATUS_KEY = "status"


class Doorbell(Device):
    def __init__(self, device_id: str, data: dict[str, Any]) -> None:
        super().__init__(device_id, data["name"], data["HouseID"])
        self._serial_number = data["serialNumber"]
        self._status = data["status"]
        recent_image = data.get("recentImage", {})
        self._image_url = recent_image.get("secure_url", None)
        self._has_subscription = data.get("dvrSubscriptionSetupDone", False)

    @cached_property
    def serial_number(self):
        return self._serial_number

    @cached_property
    def status(self):
        return self._status

    @cached_property
    def is_standby(self):
        return self.status == "standby"

    @cached_property
    def is_online(self):
        return self.status == "doorbell_call_status_online"

    @cached_property
    def image_url(self):
        return self._image_url

    @cached_property
    def has_subscription(self):
        return self._has_subscription

    def __repr__(self):
        return "Doorbell(id={}, name={}, house_id={})".format(
            self.device_id, self.device_name, self.house_id
        )


class DoorbellDetail(DeviceDetail):
    def __init__(self, data):
        super().__init__(
            data["doorbellID"],
            data["name"],
            data["HouseID"],
            data["serialNumber"],
            data["firmwareVersion"],
            data.get("pubsubChannel"),
            data,
        )

        self._status = data["status"]
        recent_image = data.get("recentImage", {})
        self._image_url = recent_image.get("secure_url", None)
        self._has_subscription = data.get("dvrSubscriptionSetupDone", False)
        self._image_created_at_datetime = None
        self._model = None

        if "type" in data:
            self._model = data["type"]

        if "created_at" in recent_image:
            self._image_created_at_datetime = parse_datetime(recent_image["created_at"])

        self._battery_level = None
        if "telemetry" in data:
            telemetry = data["telemetry"]
            if "battery_soc" in telemetry:
                self._battery_level = telemetry.get("battery_soc", None)
            elif telemetry.get("doorbell_low_battery"):
                self._battery_level = 10
            elif "battery" in telemetry:
                battery = telemetry["battery"]
                if battery >= 4:
                    self._battery_level = 100
                elif battery >= 3.75:
                    self._battery_level = 75
                elif battery >= 3.50:
                    self._battery_level = 50
                else:
                    self._battery_level = 25

    @cached_property
    def status(self):
        return self._status

    @cached_property
    def model(self):
        return self._model

    @cached_property
    def is_online(self):
        return self.status == "doorbell_call_status_online"

    @cached_property
    def is_standby(self):
        return self.status == "standby"

    @property
    def image_created_at_datetime(self):
        return self._image_created_at_datetime

    @image_created_at_datetime.setter
    def image_created_at_datetime(self, var):
        """Update the doorbell image created_at datetime (usually form the activity log)."""
        if not isinstance(var, datetime.date):
            raise ValueError
        self._image_created_at_datetime = var

    @property
    def image_url(self):
        return self._image_url

    @image_url.setter
    def image_url(self, var):
        """Update the doorbell image url (usually form the activity log)."""
        self._image_url = var

    @cached_property
    def battery_level(self):
        """Return an approximation of the battery percentage."""
        return self._battery_level

    @cached_property
    def has_subscription(self):
        return self._has_subscription

    async def async_get_doorbell_image(
        self, aiohttp_session: ClientSession, timeout=10
    ) -> bytes:
        response = await aiohttp_session.request(
            "get", self._image_url, timeout=timeout
        )
        return await response.read()

    def get_doorbell_image(self, timeout=10) -> bytes:
        return requests.get(self._image_url, timeout=timeout).content
