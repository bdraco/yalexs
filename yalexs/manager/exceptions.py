"""Exceptions for errors."""
from __future__ import annotations


class RequireValidation(Exception):
    """Error to indicate we require validation (2fa)."""


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""


class InvalidAuth(Exception):
    """Error to indicate there is invalid auth."""


class YaleXSError(Exception):
    """Base error."""
