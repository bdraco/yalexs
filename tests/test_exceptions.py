from yalexs.exceptions import (
    InvalidAuth,
    YaleApiError,
    CannotConnect,
    RequireValidation,
    YaleXSError,
    AugustApiAIOHTTPError,
)

from unittest import mock
from aiohttp import ClientResponseError


def test_exceptions_can_be_empty_for_back_compat():
    assert InvalidAuth()
    assert str(InvalidAuth()) == "InvalidAuth"
    assert YaleApiError()
    assert str(YaleApiError()) == "YaleApiError"
    assert CannotConnect()
    assert str(CannotConnect()) == "CannotConnect"
    assert RequireValidation()
    assert YaleXSError()
    assert AugustApiAIOHTTPError()


def test_august_api_aio_http_error_reraise():
    mock_client_response_error = ClientResponseError(
        mock.MagicMock(),
        mock.MagicMock(),
        status=401,
    )
    ex = AugustApiAIOHTTPError("test", mock_client_response_error)
    assert str(ex) == "test"
    assert ex.auth_failed is True
    assert ex.aiohttp_client_error is mock_client_response_error
    assert ex.args == ("test",)


def test_subclassed_august_api_aio_http_error_reraise():
    mock_client_response_error = ClientResponseError(
        mock.MagicMock(),
        mock.MagicMock(),
        status=401,
    )
    try:
        raise YaleApiError("test", mock_client_response_error)
    except AugustApiAIOHTTPError as ex:
        assert str(ex) == "test"
        assert ex.auth_failed is True
        assert ex.aiohttp_client_error is mock_client_response_error
        assert ex.args == ("test",)
