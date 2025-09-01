"""Custom exception hierarchy for Rutificador."""
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class RutError(Exception):
    """Base exception for all RUT-related errors."""

    def __init__(self, message: str, error_code: Optional[str] = None, **kwargs: Any) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = kwargs
        logger.error("RUT Error [%s]: %s", error_code, message, extra=kwargs)


class RutValidationError(RutError):
    """Base class for validation-related errors."""


class RutFormatError(RutValidationError):
    """Raised when RUT format is invalid."""

    def __init__(self, rut_value: str, expected_format: str) -> None:
        super().__init__(
            f"Invalid RUT format: '{rut_value}'. Expected format: {expected_format}",
            error_code="FORMAT_ERROR",
            rut_value=rut_value,
            expected_format=expected_format,
        )


class RutDigitError(RutValidationError):
    """Raised when verification digit is incorrect."""

    def __init__(self, provided_digit: str, calculated_digit: str) -> None:
        super().__init__(
            f"Verification digit mismatch: provided '{provided_digit}', calculated '{calculated_digit}'",
            error_code="DIGIT_ERROR",
            provided_digit=provided_digit,
            calculated_digit=calculated_digit,
        )


class RutLengthError(RutValidationError):
    """Raised when RUT length is invalid."""

    def __init__(self, rut_value: str, length: int, max_length: int) -> None:
        super().__init__(
            f"RUT '{rut_value}' exceeds maximum length: {length} > {max_length}",
            error_code="LENGTH_ERROR",
            rut_value=rut_value,
            length=length,
            max_length=max_length,
        )


class RutProcessingError(RutError):
    """Raised during batch processing operations."""


# Backward compatibility alias
RutInvalidoError = RutValidationError


__all__ = [
    "RutError",
    "RutValidationError",
    "RutFormatError",
    "RutDigitError",
    "RutLengthError",
    "RutProcessingError",
    "RutInvalidoError",
]
