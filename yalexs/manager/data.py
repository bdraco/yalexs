"""Support for August devices."""

from __future__ import annotations

import asyncio
import logging
from abc import abstractmethod
from collections.abc import Callable, Coroutine, Iterable, ValuesView
from contextlib import suppress
from datetime import datetime
from itertools import chain
from typing import Any, ParamSpec, TypeVar

from aiohttp import ClientError, ClientResponseError, ClientSession

from .._compat import cached_property
from ..activity import ActivityTypes
from ..backports.tasks import create_eager_task
from ..const import Brand
from ..doorbell import ContentTokenExpired, Doorbell, DoorbellDetail
from ..exceptions import AugustApiAIOHTTPError
from ..lock import Lock, LockDetail
from ..pubnub_activity import activities_from_pubnub_message
from ..pubnub_async import AugustPubNub
from .activity import ActivityStream
from .const import MIN_TIME_BETWEEN_DETAIL_UPDATES
from .exceptions import CannotConnect, YaleXSError
from .gateway import Gateway
from .ratelimit import _RateLimitChecker
from .socketio import SocketIORunner
from .subscriber import SubscriberMixin

_LOGGER = logging.getLogger(__name__)

API_CACHED_ATTRS = {
    "door_state",
    "door_state_datetime",
    "lock_status",
    "lock_status_datetime",
}
YALEXS_BLE_DOMAIN = "yalexs_ble"

_R = TypeVar("_R")
_P = ParamSpec("_P")


def _save_live_attrs(lock_detail: DoorbellDetail | LockDetail) -> dict[str, Any]:
    """Store the attributes that the lock detail api may have an invalid cache for.

    Since we are connected to pubnub we may have more current data
    then the api so we want to restore the most current data after
    updating battery state etc.
    """
    return {attr: getattr(lock_detail, attr) for attr in API_CACHED_ATTRS}


def _restore_live_attrs(
    lock_detail: DoorbellDetail | LockDetail, attrs: dict[str, Any]
) -> None:
    """Restore the non-cache attributes after a cached update."""
    for attr, value in attrs.items():
        setattr(lock_detail, attr, value)


class YaleXSData(SubscriberMixin):
    """YaleXS Data coordinator object."""

    def __init__(
        self, gateway: Gateway, error_exception_class: Exception = YaleXSError
    ) -> None:
        """Init August data object."""
        super().__init__(MIN_TIME_BETWEEN_DETAIL_UPDATES)
        self._gateway = gateway
        self.activity_stream: ActivityStream = None
        self._api = gateway.api
        self._device_detail_by_id: dict[str, LockDetail | DoorbellDetail] = {}
        self._doorbells_by_id: dict[str, Doorbell] = {}
        self._locks_by_id: dict[str, Lock] = {}
        self._house_ids: set[str] = set()
        self._push_unsub: Callable[[], Coroutine[Any, Any, None]] | None = None
        self._initial_sync_task: asyncio.Task | None = None
        self._error_exception_class = error_exception_class
        self._shutdown: bool = False

    @cached_property
    def brand(self) -> Brand:
        """Return the brand of the API."""
        return self._gateway.api.brand

    async def async_setup(self) -> None:
        """Async setup of august device data and activities."""
        token = await self._gateway.async_get_access_token()
        await _RateLimitChecker.check_rate_limit(token)
        await _RateLimitChecker.register_wakeup(token)

        # This used to be a gather but it was less reliable with august's recent api changes.
        locks: list[Lock] = await self._api.async_get_operable_locks(token) or []
        doorbells: list[Doorbell] = await self._api.async_get_doorbells(token) or []
        self._doorbells_by_id = {device.device_id: device for device in doorbells}
        self._locks_by_id = {device.device_id: device for device in locks}
        self._house_ids = {device.house_id for device in chain(locks, doorbells)}

        await self._async_refresh_device_detail_by_ids(
            [device.device_id for device in chain(locks, doorbells)]
        )

        # We remove all devices that we are missing
        # detail as we cannot determine if they are usable.
        # This also allows us to avoid checking for
        # detail being None all over the place
        self._remove_inoperative_locks()
        self._remove_inoperative_doorbells()
        await self.async_setup_activity_stream()

        if self._locks_by_id and self.brand is not Brand.YALE_GLOBAL:
            # Do not prevent setup as the sync can timeout
            # but it is not a fatal error as the lock
            # will recover automatically when it comes back online.
            self._initial_sync_task = create_eager_task(
                self._async_initial_sync(), name="august-initial-sync"
            )

    async def async_setup_activity_stream(self) -> None:
        """Set up the activity stream."""
        token = await self._gateway.async_get_access_token()
        user_data = await self._api.async_get_user(token)
        push: AugustPubNub | SocketIORunner
        if self.brand is Brand.YALE_GLOBAL:
            push = SocketIORunner(self._gateway)
        else:
            push = AugustPubNub()
            for device in self._device_detail_by_id.values():
                push.register_device(device)
        self.activity_stream = ActivityStream(
            self._api, self._gateway, self._house_ids, push
        )
        await self.activity_stream.async_setup()
        push.subscribe(self.async_push_message)
        self._push_unsub = await push.run(user_data["UserID"], self.brand)

    async def _async_initial_sync(self) -> None:
        """Attempt to request an initial sync."""
        # We don't care if this fails because we only want to wake
        # locks that are actually online anyways and they will be
        # awake when they come back online
        for result in await asyncio.gather(
            *[
                create_eager_task(
                    self._async_status_async(
                        device_id, bool(detail.bridge and detail.bridge.hyper_bridge)
                    )
                )
                for device_id, detail in self._device_detail_by_id.items()
                if device_id in self._locks_by_id
            ],
            return_exceptions=True,
        ):
            if isinstance(result, Exception) and not isinstance(
                result, (TimeoutError, ClientResponseError, CannotConnect)
            ):
                _LOGGER.warning(
                    "Unexpected exception during initial sync: %s",
                    result,
                    exc_info=result,
                )

    def async_push_message(
        self, device_id: str, date_time: datetime, message: dict[str, Any]
    ) -> None:
        """Process a push message."""
        device = self.get_device_detail(device_id)
        activities = activities_from_pubnub_message(device, date_time, message)
        activity_stream = self.activity_stream
        if activities and activity_stream.async_process_newer_device_activities(
            activities
        ):
            self.async_signal_device_id_update(device.device_id)
            activity_stream.async_schedule_house_id_refresh(device.house_id)

    async def async_stop(self, *args: Any) -> None:
        """Stop the subscriptions."""
        self._shutdown = True
        if self.activity_stream:
            self.activity_stream.async_stop()
        if self._initial_sync_task:
            self._initial_sync_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._initial_sync_task
        if self._push_unsub:
            await self._push_unsub()

    @property
    def doorbells(self) -> ValuesView[Doorbell]:
        """Return a list of py-august Doorbell objects."""
        return self._doorbells_by_id.values()

    @property
    def locks(self) -> ValuesView[Lock]:
        """Return a list of py-august Lock objects."""
        return self._locks_by_id.values()

    def get_device_detail(self, device_id: str) -> DoorbellDetail | LockDetail:
        """Return the py-august LockDetail or DoorbellDetail object for a device."""
        return self._device_detail_by_id[device_id]

    async def _async_refresh(self) -> None:
        """Refresh data."""
        if self._shutdown:
            return
        await self._async_refresh_device_detail_by_ids(self._subscriptions.keys())

    async def _async_refresh_device_detail_by_ids(
        self, device_ids_list: Iterable[str]
    ) -> None:
        """Refresh each device in sequence.

        This used to be a gather but it was less reliable with august's
        recent api changes.

        The august api has been timing out for some devices so
        we want the ones that it isn't timing out for to keep working.
        """
        for device_id in device_ids_list:
            try:
                await self._async_refresh_device_detail_by_id(device_id)
            except TimeoutError:  # noqa: PERF203
                _LOGGER.warning(
                    "Timed out calling august api during refresh of device: %s",
                    device_id,
                )
            except (ClientResponseError, CannotConnect) as err:
                _LOGGER.warning(
                    "Error from august api during refresh of device: %s",
                    device_id,
                    exc_info=err,
                )

    async def refresh_camera_by_id(self, device_id: str) -> None:
        """Re-fetch doorbell/camera data from API."""
        await self._async_update_device_detail(
            self._doorbells_by_id[device_id],
            self._api.async_get_doorbell_detail,
        )

    @property
    def push_updates_connected(self) -> bool:
        """Return if the push updates are connected."""
        return (
            self.activity_stream is not None
            and self.activity_stream.push_updates_connected
        )

    async def _async_refresh_device_detail_by_id(self, device_id: str) -> None:
        if self._shutdown:
            return
        if device_id in self._locks_by_id:
            if self.activity_stream and self.push_updates_connected:
                saved_attrs = _save_live_attrs(self._device_detail_by_id[device_id])
            await self._async_update_device_detail(
                self._locks_by_id[device_id], self._api.async_get_lock_detail
            )
            if self.activity_stream and self.push_updates_connected:
                _restore_live_attrs(self._device_detail_by_id[device_id], saved_attrs)
            # keypads are always attached to locks
            if (
                device_id in self._device_detail_by_id
                and self._device_detail_by_id[device_id].keypad is not None
            ):
                keypad = self._device_detail_by_id[device_id].keypad
                self._device_detail_by_id[keypad.device_id] = keypad
        elif device_id in self._doorbells_by_id:
            await self._async_update_device_detail(
                self._doorbells_by_id[device_id],
                self._api.async_get_doorbell_detail,
            )
        _LOGGER.debug(
            "async_signal_device_id_update (from detail updates): %s", device_id
        )
        self.async_signal_device_id_update(device_id)

    async def _async_update_device_detail(
        self,
        device: Doorbell | Lock,
        api_call: Callable[
            [str, str], Coroutine[Any, Any, DoorbellDetail | LockDetail]
        ],
    ) -> None:
        device_id = device.device_id
        device_name = device.device_name
        _LOGGER.debug("Started retrieving detail for %s (%s)", device_name, device_id)

        try:
            detail = await api_call(
                await self._gateway.async_get_access_token(), device_id
            )
        except ClientError as ex:
            _LOGGER.error(
                "Request error trying to retrieve %s details for %s. %s",
                device_id,
                device_name,
                ex,
            )
        _LOGGER.debug("Completed retrieving detail for %s (%s)", device_name, device_id)
        # If the key changes after startup we need to trigger a
        # discovery to keep it up to date
        if isinstance(detail, LockDetail) and detail.offline_key:
            self.async_offline_key_discovered(detail)

        self._device_detail_by_id[device_id] = detail

    @abstractmethod
    def async_offline_key_discovered(self, detail: LockDetail) -> None:
        """Handle offline key discovery."""

    def get_device(self, device_id: str) -> Doorbell | Lock | None:
        """Get a device by id."""
        return self._locks_by_id.get(device_id) or self._doorbells_by_id.get(device_id)

    def _get_device_name(self, device_id: str) -> str | None:
        """Return doorbell or lock name as August has it stored."""
        if device := self.get_device(device_id):
            return device.device_name
        return None

    async def async_lock(self, device_id: str) -> list[ActivityTypes]:
        """Lock the device."""
        return await self._async_call_api_op_requires_bridge(
            device_id,
            self._api.async_lock_return_activities,
            await self._gateway.async_get_access_token(),
            device_id,
        )

    async def async_status_async(self, device_id: str, hyper_bridge: bool) -> str:
        """Request status of the device but do not wait for a response since it will come via pubnub."""
        token = await self._gateway.async_get_access_token()
        await _RateLimitChecker.check_rate_limit(token)
        result = await self._async_status_async(device_id, hyper_bridge)
        await _RateLimitChecker.register_wakeup(token)
        return result

    async def _async_status_async(self, device_id: str, hyper_bridge: bool) -> str:
        """Request status of the device but do not wait for a response since it will come via pubnub."""
        return await self._async_call_api_op_requires_bridge(
            device_id,
            self._api.async_status_async,
            await self._gateway.async_get_access_token(),
            device_id,
            hyper_bridge,
        )

    async def async_lock_async(self, device_id: str, hyper_bridge: bool) -> str:
        """Lock the device but do not wait for a response since it will come via pubnub."""
        return await self._async_call_api_op_requires_bridge(
            device_id,
            self._api.async_lock_async,
            await self._gateway.async_get_access_token(),
            device_id,
            hyper_bridge,
        )

    async def async_unlatch(self, device_id: str) -> list[ActivityTypes]:
        """Open/unlatch the device."""
        return await self._async_call_api_op_requires_bridge(
            device_id,
            self._api.async_unlatch_return_activities,
            await self._gateway.async_get_access_token(),
            device_id,
        )

    async def async_unlatch_async(self, device_id: str, hyper_bridge: bool) -> str:
        """Open/unlatch the device but do not wait for a response since it will come via pubnub."""
        return await self._async_call_api_op_requires_bridge(
            device_id,
            self._api.async_unlatch_async,
            await self._gateway.async_get_access_token(),
            device_id,
            hyper_bridge,
        )

    async def async_unlock(self, device_id: str) -> list[ActivityTypes]:
        """Unlock the device."""
        return await self._async_call_api_op_requires_bridge(
            device_id,
            self._api.async_unlock_return_activities,
            await self._gateway.async_get_access_token(),
            device_id,
        )

    async def async_unlock_async(self, device_id: str, hyper_bridge: bool) -> str:
        """Unlock the device but do not wait for a response since it will come via pubnub."""
        return await self._async_call_api_op_requires_bridge(
            device_id,
            self._api.async_unlock_async,
            await self._gateway.async_get_access_token(),
            device_id,
            hyper_bridge,
        )

    async def _async_call_api_op_requires_bridge(
        self,
        device_id: str,
        func: Callable[_P, Coroutine[Any, Any, _R]],
        *args: _P.args,
        **kwargs: _P.kwargs,
    ) -> _R:
        """Call an API that requires the bridge to be online and will change the device state."""
        try:
            ret = await func(*args, **kwargs)
        except AugustApiAIOHTTPError as err:
            device_name = self._get_device_name(device_id)
            if device_name is None:
                device_name = f"DeviceID: {device_id}"
            raise self._error_exception_class(f"{device_name}: {err}") from err

        return ret

    async def async_get_doorbell_image(
        self,
        device_id: str,
        aiohttp_session: ClientSession,
        timeout: float = 10.0,
    ) -> bytes:
        """Get the latest image from the doorbell."""
        doorbell = self.get_device_detail(device_id)
        try:
            return await doorbell.async_get_doorbell_image(aiohttp_session, timeout)
        except ContentTokenExpired:
            if self.brand not in (Brand.YALE_HOME, Brand.YALE_GLOBAL):
                raise
            _LOGGER.debug(
                "Error fetching camera image, updating content-token from api to retry"
            )
            await self.refresh_camera_by_id(device_id)
            doorbell = self.get_device_detail(device_id)
            return await doorbell.async_get_doorbell_image(aiohttp_session, timeout)

    def _remove_inoperative_doorbells(self) -> None:
        for doorbell in list(self.doorbells):
            device_id = doorbell.device_id
            if self._device_detail_by_id.get(device_id):
                continue
            _LOGGER.info(
                (
                    "The doorbell %s could not be setup because the system could not"
                    " fetch details about the doorbell"
                ),
                doorbell.device_name,
            )
            del self._doorbells_by_id[device_id]

    def _remove_inoperative_locks(self) -> None:
        # Remove non-operative locks as there must
        # be a bridge (August Connect) for them to
        # be usable
        for lock in list(self.locks):
            device_id = lock.device_id
            lock_detail = self._device_detail_by_id.get(device_id)
            if lock_detail is None:
                _LOGGER.info(
                    (
                        "The lock %s could not be setup because the system could not"
                        " fetch details about the lock"
                    ),
                    lock.device_name,
                )
            elif lock_detail.bridge is None:
                _LOGGER.info(
                    (
                        "The lock %s could not be setup because it does not have a"
                        " bridge (Connect)"
                    ),
                    lock.device_name,
                )
                del self._device_detail_by_id[device_id]
            # Bridge may come back online later so we still add the device since we will
            # have a pubnub subscription to tell use when it recovers
            else:
                continue
            del self._locks_by_id[device_id]
