from typing import Any, Dict, Optional

from .backports.functools import cached_property

USER_CACHE = {}


class YaleUser:
    """Represent a yale access user."""

    def __init__(self, uuid: str, data: Dict[str, Any]) -> None:
        """Initialize the YaleUser."""
        self._uuid = uuid
        self._data = data

    @cached_property
    def thumbnail_url(self) -> Optional[str]:
        return self._data.get("imageInfo", {}).get("thumbnail", {}).get("secure_url")

    @cached_property
    def image_url(self) -> Optional[str]:
        return self._data.get("imageInfo", {}).get("original", {}).get("secure_url")

    @cached_property
    def first_name(self) -> Optional[str]:
        return self._data.get("FirstName")

    @cached_property
    def last_name(self) -> Optional[str]:
        return self._data.get("LastName")

    @cached_property
    def user_type(self) -> Optional[str]:
        return self._data.get("UserType")


def get_user_info(uuid: str) -> Optional[YaleUser]:
    return USER_CACHE.get(uuid)


def cache_user_info(uuid: str, data: Dict[str, Any]) -> None:
    if uuid not in USER_CACHE:
        USER_CACHE[uuid] = YaleUser(uuid, data)
