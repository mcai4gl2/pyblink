"""Custom exceptions for the Blink runtime."""

class BlinkError(Exception):
    """Base exception for all Blink-related errors."""


class SchemaError(BlinkError):
    """Raised when schema parsing or resolution fails."""


class EncodeError(BlinkError):
    """Raised when message encoding fails."""


class DecodeError(BlinkError):
    """Raised when encoded data cannot be decoded."""


class RegistryError(BlinkError):
    """Raised for registry lookup issues."""
