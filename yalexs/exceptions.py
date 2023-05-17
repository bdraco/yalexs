from http import HTTPStatus

from aiohttp import ClientResponseError
from requests.exceptions import HTTPError


class AugustApiAIOHTTPError(Exception):
    """An yale access api error with a friendly user consumable string."""

    def __init__(
        self, message: str, aiohttp_client_response_exception: ClientResponseError
    ) -> None:
        """Initialize the error."""
        super().__init__(message)
        self.status = aiohttp_client_response_exception.status
        self.auth_failed = self.status in (
            HTTPStatus.UNAUTHORIZED,
            HTTPStatus.FORBIDDEN,
        )


class AugustApiHTTPError(HTTPError):
    """An yale access api error with a friendly user consumable string."""
