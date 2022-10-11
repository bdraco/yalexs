from typing import Any, Optional

USER_CACHE = {}


class YaleUser:
    """Represent a yale access user."""

    def __init__(self, uuid: str, data: dict[str, Any]) -> None:
        """Initialize the YaleUser."""
        self._uuid = uuid
        self._data = data

    @property
    def thumbnail_url(self) -> Optional[str]:
        return self._data.get("imageInfo", {}).get("thumbnail", {}).get("secure_url")

    @property
    def image_url(self) -> Optional[str]:
        return self._data.get("imageInfo", {}).get("original", {}).get("secure_url")

    @property
    def first_name(self) -> Optional[str]:
        return self._data.get("FirstName")

    @property
    def last_name(self) -> Optional[str]:
        return self._data.get("LastName")

    @property
    def user_type(self) -> Optional[str]:
        return self._data.get("UserType")


def get_user_info(uuid: str) -> Optional[YaleUser]:
    return USER_CACHE.get(uuid)


def cache_user_info(uuid: str, data: dict[str, Any]):
    if uuid not in USER_CACHE:
        USER_CACHE[uuid] = YaleUser(uuid, data)
