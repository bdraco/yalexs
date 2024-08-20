from __future__ import annotations

from http import HTTPStatus

from aiohttp import ClientError, ClientResponseError


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


class YaleApiError(AugustApiAIOHTTPError):
    """An yale access api error with a friendly user consumable string."""


class RequireValidation(Exception):
    """Error to indicate we require validation (2fa)."""


class CannotConnect(YaleApiError):
    """Error to indicate we cannot connect."""


class InvalidAuth(YaleApiError):
    """Error to indicate there is invalid auth."""


class YaleXSError(Exception):
    """Base error."""


class ContentTokenExpired(Exception):
    """Token required for accessing this resource is not valid."""
