from __future__ import annotations

from http import HTTPStatus

from aiohttp import ClientError, ClientResponseError
from requests.exceptions import HTTPError


class AugustApiAIOHTTPError(Exception):
    """An yale access api error with a friendly user consumable string."""

    def __init__(self, message: str, aiohttp_client_error: ClientError) -> None:
        """Initialize the error."""
        super().__init__(message)
        self.status = (
            isinstance(aiohttp_client_error, ClientResponseError)
            and aiohttp_client_error.status
        )
        self.auth_failed = self.status in (
            HTTPStatus.UNAUTHORIZED,
            HTTPStatus.FORBIDDEN,
        )


class AugustApiHTTPError(HTTPError):
    """An yale access api error with a friendly user consumable string."""


class ContentTokenExpired(Exception):
    """Token required for accessing this resource is not valid."""
