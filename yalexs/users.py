from __future__ import annotations

from typing import Any

from .backports.functools import cached_property

USER_CACHE = {}


class YaleUser:
    """Represent a yale access user."""

    def __init__(self, uuid: str, data: dict[str, Any]) -> None:
        """Initialize the YaleUser."""
        self._uuid = uuid
        self._data = data

    @cached_property
    def thumbnail_url(self) -> str | None:
        return self._data.get("imageInfo", {}).get("thumbnail", {}).get("secure_url")

    @cached_property
    def image_url(self) -> str | None:
        return self._data.get("imageInfo", {}).get("original", {}).get("secure_url")

    @cached_property
    def first_name(self) -> str | None:
        return self._data.get("FirstName")

    @cached_property
    def last_name(self) -> str | None:
        return self._data.get("LastName")

    @cached_property
    def user_type(self) -> str | None:
        return self._data.get("UserType")


def get_user_info(uuid: str) -> YaleUser | None:
    return USER_CACHE.get(uuid)


def cache_user_info(uuid: str, data: dict[str, Any]) -> None:
    if uuid not in USER_CACHE:
        USER_CACHE[uuid] = YaleUser(uuid, data)
