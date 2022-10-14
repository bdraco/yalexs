from datetime import datetime, timedelta, timezone

from dateutil.tz import tzutc
from httpx import RequestError, Response
import pytest

from yalexs.api_async import ApiAsync
from yalexs.api_common import (
    API_GET_HOUSES_URL,
    API_GET_SESSION_URL,
    API_SEND_VERIFICATION_CODE_URLS,
    API_VALIDATE_VERIFICATION_CODE_URLS,
    HEADER_AUGUST_ACCESS_TOKEN,
)
from yalexs.authenticator_async import (
    AuthenticationState,
    AuthenticatorAsync,
    ValidationResult,
)

pytestmark = pytest.mark.asyncio


def format_datetime(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + "Z"


async def _async_create_authenticator_async(httpx_client, respx_mock):
    authenticator = AuthenticatorAsync(
        ApiAsync(httpx_client), "phone", "user", "pass", install_id="install_id"
    )
    await authenticator.async_setup_authentication()
    return authenticator


def _setup_session_response(
    mock,
    v_password,
    v_install_id,
    expires_at=format_datetime(datetime.utcnow()),
):
    mock.post(API_GET_SESSION_URL).mock(
        Response(
            status_code=200,
            headers={"x-august-access-token": "access_token"},
            json={
                "expiresAt": expires_at,
                "vPassword": v_password,
                "vInstallId": v_install_id,
            },
        )
    )


async def test_async_should_refresh_when_token_expiry_is_after_renewal_threshold(
    httpx_client, respx_mock
):
    expired_expires_at = format_datetime(datetime.now(timezone.utc) + timedelta(days=6))
    _setup_session_response(respx_mock, True, True, expires_at=expired_expires_at)

    authenticator = await _async_create_authenticator_async(httpx_client, respx_mock)
    await authenticator.async_authenticate()

    should_refresh = authenticator.should_refresh()
    assert should_refresh is True


async def test_async_should_refresh_when_token_expiry_is_before_renewal_threshold(
    httpx_client, respx_mock
):
    not_expired_expires_at = format_datetime(
        datetime.now(timezone.utc) + timedelta(days=8)
    )
    _setup_session_response(respx_mock, True, True, expires_at=not_expired_expires_at)

    authenticator = await _async_create_authenticator_async(httpx_client, respx_mock)
    await authenticator.async_authenticate()

    should_refresh = authenticator.should_refresh()

    assert should_refresh is False


async def test_async_refresh_token(httpx_client, respx_mock):
    _setup_session_response(respx_mock, True, True)

    authenticator = await _async_create_authenticator_async(httpx_client, respx_mock)
    await authenticator.async_authenticate()

    token = "e30=.eyJleHAiOjEzMzd9.e30="
    respx_mock.get(API_GET_HOUSES_URL).mock(
        Response(200, text=token, headers={HEADER_AUGUST_ACCESS_TOKEN: token})
    )

    access_token = await authenticator.async_refresh_access_token(force=False)

    assert access_token.access_token == token
    assert access_token.parsed_expiration_time() == datetime.fromtimestamp(
        1337, tz=tzutc()
    )


async def test_async_get_session_with_authenticated_response(httpx_client, respx_mock):
    _setup_session_response(respx_mock, True, True)

    authenticator = await _async_create_authenticator_async(httpx_client, respx_mock)
    authentication = await authenticator.async_authenticate()

    assert authentication.access_token == "access_token"
    assert authentication.install_id == "install_id"
    assert authentication.state == AuthenticationState.AUTHENTICATED


async def test_async_get_session_with_bad_password_response(httpx_client, respx_mock):
    _setup_session_response(respx_mock, False, True)

    authenticator = await _async_create_authenticator_async(httpx_client, respx_mock)
    authentication = await authenticator.async_authenticate()

    assert authentication.access_token == "access_token"
    assert authentication.install_id == "install_id"
    assert authentication.state == AuthenticationState.BAD_PASSWORD


async def test_async_get_session_with_requires_validation_response(
    httpx_client, respx_mock
):
    _setup_session_response(respx_mock, True, False)

    authenticator = await _async_create_authenticator_async(httpx_client, respx_mock)
    authentication = await authenticator.async_authenticate()

    assert authentication.access_token == "access_token"
    assert authentication.install_id == "install_id"
    assert authentication.state == AuthenticationState.REQUIRES_VALIDATION


async def test_async_get_session_with_already_authenticated_state(
    httpx_client, respx_mock
):
    _setup_session_response(respx_mock, True, True)

    authenticator = await _async_create_authenticator_async(httpx_client, respx_mock)
    # this will set authentication state to AUTHENTICATED
    await authenticator.async_authenticate()
    # call authenticate() again
    authentication = await authenticator.async_authenticate()

    assert authentication.access_token == "access_token"
    assert authentication.install_id == "install_id"
    assert authentication.state == AuthenticationState.AUTHENTICATED


async def test_async_send_verification_code(httpx_client, respx_mock):
    _setup_session_response(respx_mock, True, False)

    authenticator = await _async_create_authenticator_async(httpx_client, respx_mock)
    respx_mock.post(API_SEND_VERIFICATION_CODE_URLS["phone"]).mock(
        Response(200, json={})
    )
    await authenticator.async_authenticate()
    result = await authenticator.async_send_verification_code()

    assert result is True


async def test_async_validate_verification_code_with_no_code(httpx_client, respx_mock):
    _setup_session_response(respx_mock, True, False)

    authenticator = await _async_create_authenticator_async(httpx_client, respx_mock)
    await authenticator.async_authenticate()

    respx_mock.post(API_VALIDATE_VERIFICATION_CODE_URLS["phone"]).mock(
        Response(200, json={})
    )
    result = await authenticator.async_validate_verification_code("")

    # respx_mock.async_validate_verification_code.assert_not_called()
    assert result == ValidationResult.INVALID_VERIFICATION_CODE


async def test_async_validate_verification_code_with_validated_response(
    httpx_client, respx_mock
):
    _setup_session_response(respx_mock, True, False)

    respx_mock.post(API_VALIDATE_VERIFICATION_CODE_URLS["phone"]).mock(
        Response(200, json={})
    )

    authenticator = await _async_create_authenticator_async(httpx_client, respx_mock)
    await authenticator.async_authenticate()
    result = await authenticator.async_validate_verification_code("123456")

    assert result == ValidationResult.VALIDATED


async def test_async_validate_verification_code_with_invalid_code_response(
    httpx_client, respx_mock
):
    _setup_session_response(respx_mock, True, False)

    respx_mock.post(API_VALIDATE_VERIFICATION_CODE_URLS["phone"]).mock(
        side_effect=RequestError("any")
    )

    authenticator = await _async_create_authenticator_async(httpx_client, respx_mock)
    await authenticator.async_authenticate()
    result = await authenticator.async_validate_verification_code("123456")

    assert result == ValidationResult.INVALID_VERIFICATION_CODE
