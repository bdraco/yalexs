from requests.exceptions import HTTPError


class AugustApiAIOHTTPError(Exception):
    """An yale access api error with a friendly user consumable string."""


class AugustApiHTTPError(HTTPError):
    """An yale access api error with a friendly user consumable string."""
