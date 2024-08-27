"""Consume the august activity stream."""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from time import monotonic

from aiohttp import ClientError

from ..activity import Activity, ActivityType
from ..api_async import ApiAsync
from ..backports.tasks import create_eager_task
from ..pubnub_async import AugustPubNub
from ..util import get_latest_activity
from .const import ACTIVITY_UPDATE_INTERVAL
from .gateway import Gateway
from .subscriber import SubscriberMixin
from .socketio import SocketIORunner

_LOGGER = logging.getLogger(__name__)

ACTIVITY_STREAM_FETCH_LIMIT = 10
ACTIVITY_CATCH_UP_FETCH_LIMIT = 2500

INITIAL_LOCK_RESYNC_TIME = 60

# If there is a storm of activity (ie lock, unlock, door open, door close, etc)
# we want to debounce the updates so we don't hammer the activity api too much.
ACTIVITY_DEBOUNCE_COOLDOWN = 4


def _async_cancel_future_scheduled_updates(cancels: list[asyncio.TimerHandle]) -> None:
    """Cancel future scheduled updates."""
    for cancel in cancels:
        cancel.cancel()
    cancels.clear()


class ActivityStream(SubscriberMixin):
    """August activity stream handler."""

    def __init__(
        self,
        api: ApiAsync,
        august_gateway: Gateway,
        house_ids: set[str],
        push: AugustPubNub | SocketIORunner,
    ) -> None:
        """Init activity stream object."""
        super().__init__(ACTIVITY_UPDATE_INTERVAL)
        self._schedule_updates: dict[str, list[asyncio.TimerHandle]] = defaultdict(list)
        self._august_gateway = august_gateway
        self._api = api
        self._house_ids = house_ids
        self._latest_activities: defaultdict[
            str, dict[ActivityType, Activity | None]
        ] = defaultdict(lambda: defaultdict(lambda: None))
        self._did_first_update = False
        self.push = push
        self._update_tasks: dict[str, asyncio.Task] = {}
        self._start_time: float | None = None
        self._loop = asyncio.get_running_loop()
        self._shutdown: bool = False

    async def async_setup(self) -> None:
        """Token refresh check and catch up the activity stream."""
        self._start_time = monotonic()
        await self._async_refresh()
        await self._async_first_refresh()
        self._did_first_update = True

    def async_stop(self) -> None:
        """Cleanup any debounces."""
        self._shutdown = True
        for task in self._update_tasks.values():
            task.cancel()
        self._update_tasks.clear()
        self._async_cancel_future_updates()

    def _async_cancel_future_updates(self) -> None:
        """Cancel future updates."""
        for cancels in self._schedule_updates.values():
            _async_cancel_future_scheduled_updates(cancels)

    def get_latest_device_activity(
        self, device_id: str, activity_types: set[ActivityType]
    ) -> Activity | None:
        """Return latest activity that is one of the activity_types."""
        if not (latest_device_activities := self._latest_activities.get(device_id)):
            return None

        latest_activity: Activity | None = None

        for activity_type in activity_types:
            if activity := latest_device_activities.get(activity_type):
                if (
                    latest_activity
                    and activity.activity_start_time
                    <= latest_activity.activity_start_time
                ):
                    continue
                latest_activity = activity

        return latest_activity

    @property
    def push_updates_connected(self) -> bool:
        """Return if the push updates are connected."""
        return self.push.connected

    async def _async_refresh(self) -> None:
        """Update the activity stream from August."""
        # This is the only place we refresh the api token
        if self._shutdown:
            return
        self._async_cancel_future_updates()
        await self._august_gateway.async_refresh_access_token_if_needed()
        if not self.push_updates_connected:
            _LOGGER.debug("Push updates are not connected, data will be stale")

    async def _async_first_refresh(self) -> None:
        """Update the activity stream from August for the first time."""
        if self.push_updates_connected:
            _LOGGER.debug("Skipping update because push updates are active")
            return
        _LOGGER.debug("Start retrieving device activities")
        # Await in sequence to avoid hammering the API
        for house_id in self._house_ids:
            if (
                current_task := self._update_tasks.get(house_id)
            ) and not current_task.done():
                continue
            await self._async_update_house_id(house_id)

    def _async_future_update(self, house_id: str) -> None:
        """Update the activity stream from August in the future."""
        if self._shutdown:
            return
        if (
            current_task := self._update_tasks.get(house_id)
        ) and not current_task.done():
            self._loop.call_later(
                ACTIVITY_DEBOUNCE_COOLDOWN, self._async_future_update, house_id
            )
            return
        self._update_tasks[house_id] = create_eager_task(
            self._async_update_house_id(house_id), loop=self._loop
        )

    def async_schedule_house_id_refresh(self, house_id: str) -> None:
        """Update for a house activities now and once in the future."""
        self._async_cancel_future_updates()
        self._async_future_update(house_id)
        # Schedule two updates past the debounce time
        # to ensure we catch the case where the activity
        # api does not update right away and we need to poll
        # it again. Sometimes the lock operator or a doorbell
        # will not show up in the activity stream right away.
        # Only do additional polls if we are past
        # the initial lock resync time to avoid a storm
        # of activity at setup.
        if (
            not self._start_time
            or monotonic() - self._start_time < INITIAL_LOCK_RESYNC_TIME
        ):
            _LOGGER.debug(
                "Skipping additional updates due to ongoing initial lock resync time"
            )
            return

        _LOGGER.debug("Scheduling additional updates for house id %s", house_id)
        self._schedule_updates[house_id].extend(
            self._loop.call_later(
                (step * ACTIVITY_DEBOUNCE_COOLDOWN) + 0.1,
                self._async_future_update,
                house_id,
            )
            for step in (1, 2)
        )

    async def _async_update_house_id(self, house_id: str) -> None:
        """Update device activities for a house."""
        if self._shutdown:
            return

        if self._did_first_update:
            limit = ACTIVITY_STREAM_FETCH_LIMIT
        else:
            limit = ACTIVITY_CATCH_UP_FETCH_LIMIT

        _LOGGER.debug("Updating device activity for house id %s", house_id)
        try:
            activities = await self._api.async_get_house_activities(
                await self._august_gateway.async_get_access_token(),
                house_id,
                limit=limit,
            )
        except ClientError as ex:
            _LOGGER.error(
                "Request error trying to retrieve activity for house id %s: %s",
                house_id,
                ex,
            )
            # Make sure we process the next house if one of them fails
            return

        _LOGGER.debug(
            "Completed retrieving device activities for house id %s", house_id
        )
        for device_id in self.async_process_newer_device_activities(activities):
            _LOGGER.debug(
                "async_signal_device_id_update (from activity stream): %s",
                device_id,
            )
            self.async_signal_device_id_update(device_id)

    def async_process_newer_device_activities(
        self, activities: list[Activity]
    ) -> set[str]:
        """Process activities if they are newer than the last one."""
        updated_device_ids: set[str] = set()
        latest_activities = self._latest_activities
        for activity in activities:
            device_id = activity.device_id
            activity_type = activity.activity_type
            device_activities = latest_activities[device_id]
            # Ignore activities that are older than the latest one unless it is a non
            # locking or unlocking activity with the exact same start time.
            last_activity = device_activities[activity_type]
            # The activity stream can have duplicate activities. So we need
            # to call get_latest_activity to figure out if if the activity
            # is actually newer than the last one.
            latest_activity = get_latest_activity(activity, last_activity)
            if latest_activity != activity:
                continue

            device_activities[activity_type] = activity
            updated_device_ids.add(device_id)

        return updated_device_ids
