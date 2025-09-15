"""Jerarquía de excepciones personalizadas para Rutificador."""
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ErrorRut(Exception):
    """Excepción base para todos los errores relacionados con RUT."""

    def __init__(
        self, message: str, error_code: Optional[str] = None, **kwargs: Any
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.contexto = kwargs
        logger.error("Error de RUT [%s]: %s", error_code, message, extra=kwargs)


class ErrorValidacionRut(ErrorRut):
    """Excepción base para errores relacionados con la validación."""


class ErrorFormatoRut(ErrorValidacionRut):
    """Se lanza cuando el formato del RUT es inválido."""

    def __init__(self, valor_rut: str, formato_esperado: str) -> None:
        super().__init__(
            f"Formato de RUT inválido: '{valor_rut}'. "
            f"Formato esperado: {formato_esperado}",
            error_code="FORMAT_ERROR",
            rut_value=valor_rut,
            expected_format=formato_esperado,
        )


class ErrorDigitoRut(ErrorValidacionRut):
    """Se lanza cuando el dígito verificador es incorrecto."""

    def __init__(self, digito_entregado: str, digito_calculado: str) -> None:
        super().__init__(
            f"Dígito verificador no coincide: se entregó '{digito_entregado}', "
            f"se calculó '{digito_calculado}'",
            error_code="DIGIT_ERROR",
            provided_digit=digito_entregado,
            calculated_digit=digito_calculado,
        )


class ErrorLongitudRut(ErrorValidacionRut):
    """Se lanza cuando la longitud del RUT es inválida."""

    def __init__(self, valor_rut: str, longitud: int, longitud_maxima: int) -> None:
        super().__init__(
            f"El RUT '{valor_rut}' excede la longitud máxima: "
            f"{longitud} > {longitud_maxima}",
            error_code="LENGTH_ERROR",
            rut_value=valor_rut,
            length=longitud,
            max_length=longitud_maxima,
        )


class ErrorProcesamientoRut(ErrorRut):
    """Se lanza durante operaciones de procesamiento por lotes."""


# Alias para compatibilidad retroactiva
RutInvalidoError = ErrorValidacionRut
RutError = ErrorRut
RutValidationError = ErrorValidacionRut
RutFormatError = ErrorFormatoRut
RutDigitError = ErrorDigitoRut
RutLengthError = ErrorLongitudRut
RutProcessingError = ErrorProcesamientoRut


__all__ = [
    "ErrorRut",
    "ErrorValidacionRut",
    "ErrorFormatoRut",
    "ErrorDigitoRut",
    "ErrorLongitudRut",
    "ErrorProcesamientoRut",
    "RutInvalidoError",
    # Alias legados
    "RutError",
    "RutValidationError",
    "RutFormatError",
    "RutDigitError",
    "RutLengthError",
    "RutProcessingError",
]
