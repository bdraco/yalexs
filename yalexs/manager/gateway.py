"""Handle connection setup and authentication."""

from __future__ import annotations

import asyncio
import logging
import os
from http import HTTPStatus
from pathlib import Path
from typing import TypedDict

from aiohttp import ClientError, ClientResponseError, ClientSession

from ..api_async import ApiAsync
from ..authenticator_async import AuthenticationState, AuthenticatorAsync
from ..authenticator_common import Authentication
from ..const import DEFAULT_BRAND
from ..exceptions import AugustApiAIOHTTPError, RateLimited
from .const import (
    CONF_ACCESS_TOKEN_CACHE_FILE,
    CONF_BRAND,
    CONF_INSTALL_ID,
    CONF_LOGIN_METHOD,
    CONF_PASSWORD,
    CONF_TIMEOUT,
    CONF_USERNAME,
    DEFAULT_AUGUST_CONFIG_FILE,
    DEFAULT_TIMEOUT,
    VERIFICATION_CODE_KEY,
)
from .exceptions import CannotConnect, InvalidAuth, RequireValidation
from .ratelimit import _RateLimitChecker

_LOGGER = logging.getLogger(__name__)


class Config(TypedDict):
    """Config for the gateway."""

    username: str
    password: str
    login_method: str
    access_token_cache_file: str
    install_id: str
    brand: str
    timeout: int


class Gateway:
    """Handle the connection to yale."""

    api: ApiAsync
    authenticator: AuthenticatorAsync
    authentication: Authentication
    _access_token_cache_file: str

    def __init__(self, config_path: Path, aiohttp_session: ClientSession) -> None:
        """Init the connection."""
        self._aiohttp_session = aiohttp_session
        self._token_refresh_lock = asyncio.Lock()
        self._config_path = config_path
        self._config: Config | None = None
        self._loop = asyncio.get_running_loop()

    async def async_get_access_token(self) -> str:
        """Get the access token."""
        return self.authentication.access_token

    def async_configure_access_token_cache_file(
        self, username: str, access_token_cache_file: str | None
    ) -> str:
        """Configure the access token cache file."""
        file = access_token_cache_file or f".{username}{DEFAULT_AUGUST_CONFIG_FILE}"
        self._access_token_cache_file = file
        return self._config_path.joinpath(file)

    async def async_setup(
        self, conf: Config, authenticator_class: type[AuthenticatorAsync] | None = None
    ) -> None:
        """Create the api and authenticator objects."""
        if conf.get(VERIFICATION_CODE_KEY):
            return

        self._config = conf
        self.api = ApiAsync(
            self._aiohttp_session,
            timeout=self._config.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
            brand=self._config.get(CONF_BRAND, DEFAULT_BRAND),
        )
        klass = authenticator_class or AuthenticatorAsync
        username = conf.get(CONF_USERNAME)
        access_token_cache_file_path: str | None = None
        if username:
            access_token_cache_file_path = self.async_configure_access_token_cache_file(
                conf[CONF_USERNAME], conf.get(CONF_ACCESS_TOKEN_CACHE_FILE)
            )

        self.authenticator = klass(
            self.api,
            self._config.get(CONF_LOGIN_METHOD),
            username,
            self._config.get(CONF_PASSWORD, ""),
            install_id=self._config.get(CONF_INSTALL_ID),
            access_token_cache_file=access_token_cache_file_path,
        )

        await self.authenticator.async_setup_authentication()

    async def async_authenticate(self) -> Authentication:  # noqa: C901
        """Authenticate with the details provided to setup."""
        try:
            self.authentication = await self.authenticator.async_authenticate()
            token = await self.async_get_access_token()
            await _RateLimitChecker.check_rate_limit(token)
            auth_state = self.authentication.state
            if auth_state is AuthenticationState.AUTHENTICATED:
                # Call the locks api to verify we are actually
                # authenticated because we can be authenticated
                # by have no access
                await self.api.async_get_operable_locks(
                    await self.async_get_access_token()
                )
        except RateLimited:
            raise
        except AugustApiAIOHTTPError as ex:
            if ex.auth_failed:
                raise InvalidAuth(ex.args[0], ex.aiohttp_client_error) from ex
            raise CannotConnect(ex.args[0], ex.aiohttp_client_error) from ex
        except ClientResponseError as ex:
            if ex.status == HTTPStatus.UNAUTHORIZED:
                raise InvalidAuth(ex.args[0], ex) from ex

            raise CannotConnect(ex.args[0], ex) from ex
        except ClientError as ex:
            _LOGGER.error("Unable to connect to August service: %s", str(ex))
            raise CannotConnect(ex.args[0], ex) from ex

        if auth_state is AuthenticationState.BAD_PASSWORD:
            raise InvalidAuth

        if auth_state is AuthenticationState.REQUIRES_VALIDATION:
            raise RequireValidation

        if auth_state is not AuthenticationState.AUTHENTICATED:
            _LOGGER.error("Unknown authentication state: %s", auth_state)
            raise InvalidAuth

        return self.authentication

    async def async_reset_authentication(self) -> None:
        """Remove the cache file."""
        await self._loop.run_in_executor(None, self._reset_authentication)

    def _reset_authentication(self) -> None:
        """Remove the cache file."""
        path = self._config_path.joinpath(self._access_token_cache_file)
        if os.path.exists(path):
            os.unlink(path)

    async def async_refresh_access_token_if_needed(self) -> None:
        """Refresh the august access token if needed."""
        if not self.authenticator.should_refresh():
            return
        async with self._token_refresh_lock:
            refreshed_authentication = (
                await self.authenticator.async_refresh_access_token(force=False)
            )
            _LOGGER.info(
                (
                    "Refreshed august access token. The old token expired at %s, and"
                    " the new token expires at %s"
                ),
                self.authentication.access_token_expires,
                refreshed_authentication.access_token_expires,
            )
            self.authentication = refreshed_authentication
