"""yalexs subscribers."""
from __future__ import annotations

import asyncio
from abc import abstractmethod
from datetime import timedelta
from typing import Any, Callable


class SubscriberMixin:
    """Base implementation for a subscriber."""

    def __init__(self, update_interval: timedelta) -> None:
        """Initialize an subscriber."""
        super().__init__()
        self._update_interval_seconds = update_interval.total_seconds()
        self._subscriptions: dict[str, list[Callable[[], None]]] = {}
        self._unsub_interval: asyncio.TimerHandle | None = None
        self._loop = asyncio.get_running_loop()
        self._refresh_task: asyncio.Task | None = None

    def async_subscribe_device_id(
        self, device_id: str, update_callback: Callable[[], None]
    ) -> Callable[[], None]:
        """Add an callback subscriber.

        Returns a callable that can be used to unsubscribe.
        """
        if not self._subscriptions:
            self._async_setup_listeners()

        self._subscriptions.setdefault(device_id, []).append(update_callback)

        def _unsubscribe() -> None:
            self.async_unsubscribe_device_id(device_id, update_callback)

        return _unsubscribe

    @abstractmethod
    async def _async_refresh(self) -> None:
        """Refresh data."""

    def _async_scheduled_refresh(self) -> None:
        """Call the refresh method."""
        self._unsub_interval = self._loop.call_later(
            self._update_interval_seconds,
            self._async_scheduled_refresh,
        )
        self._refresh_task = asyncio.create_task(
            self._async_refresh(), name=f"{self} schedule refresh"
        )

    def _async_cancel_update_interval(self) -> None:
        """Cancel the scheduled update."""
        if self._unsub_interval:
            self._unsub_interval.cancel()
            self._unsub_interval = None

    def _async_setup_listeners(self) -> None:
        """Create interval and stop listeners."""
        self._async_cancel_update_interval()
        self._unsub_interval = self._loop.call_later(
            self._update_interval_seconds,
            self._async_scheduled_refresh,
        )

    def async_stop(self, *args: Any) -> None:
        """Cleanup on shutdown."""
        self._refresh_task.cancel()
        self._async_cancel_update_interval()

    def async_unsubscribe_device_id(
        self, device_id: str, update_callback: Callable[[], None]
    ) -> None:
        """Remove a callback subscriber."""
        self._subscriptions[device_id].remove(update_callback)
        if not self._subscriptions[device_id]:
            del self._subscriptions[device_id]

        if self._subscriptions:
            return
        self._async_cancel_update_interval()

    def async_signal_device_id_update(self, device_id: str) -> None:
        """Call the callbacks for a device_id."""
        if not self._subscriptions.get(device_id):
            return

        for update_callback in self._subscriptions[device_id]:
            update_callback()
