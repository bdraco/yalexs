from __future__ import annotations

from enum import Enum
from typing import Any

from .backports.functools import cached_property
from .device import DeviceDetail


class BridgeStatus(Enum):
    OFFLINE = "offline"
    ONLINE = "online"
    UNKNOWN = "unknown"


class BridgeDetail(DeviceDetail):
    """Represents a bridge device."""

    def __init__(self, house_id: str, data: dict[str, Any]) -> None:
        """Initialize the bridge device."""
        super().__init__(
            data["_id"], None, house_id, None, data["firmwareVersion"], None, data
        )

        self._hyper_bridge = data.get("hyperBridge", False)
        self._operative = data["operative"]

        if "status" in data:
            self._status = BridgeStatusDetail(data["status"])
        else:
            self._status = None

    @property
    def status(self):
        return self._status

    @cached_property
    def hyper_bridge(self):
        return self._hyper_bridge

    @cached_property
    def operative(self):
        return self._operative

    def set_online(self, state):
        """Called when the bridge online state changes."""
        self._status.set_online(state)


class BridgeStatusDetail:
    """Represents the status of a bridge device."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Initialize the bridge status."""
        self._current = BridgeStatus.UNKNOWN

        if "current" in data and data["current"] == "online":
            self._current = BridgeStatus.ONLINE

        self._updated = data["updated"] if "updated" in data else None
        self._last_online = data["lastOnline"] if "lastOnline" in data else None
        self._last_offline = data["lastOffline"] if "lastOffline" in data else None

    @property
    def current(self):
        return self._current

    def set_online(self, state):
        """Called when the bridge online state changes."""
        self._current = BridgeStatus.ONLINE if state else BridgeStatus.OFFLINE

    @cached_property
    def updated(self):
        return self._updated

    @cached_property
    def last_online(self):
        return self._last_online

    @cached_property
    def last_offline(self):
        return self._last_offline
