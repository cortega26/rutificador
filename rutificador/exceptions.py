"""Jerarquía de excepciones personalizadas para Rutificador."""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ErrorRut(Exception):
    """Excepción base para todos los errores relacionados con RUT."""

    def __init__(
        self, mensaje: str, codigo_error: Optional[str] = None, **kwargs: Any
    ) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.codigo_error = codigo_error
        # Sanitizar valores PII (RUT) de los metadatos antes de loguear
        self.contexto = {
            k: ("********" if "rut" in k.lower() else v) for k, v in kwargs.items()
        }
        # Evitar registrar valores completos de RUT en logs por defecto.
        logger.error("Error de RUT [%s]", codigo_error, extra=self.contexto)


class ErrorValidacionRut(ErrorRut):
    """Excepción base para errores relacionados con la validación."""


class ErrorFormatoRut(ErrorValidacionRut):
    """Se lanza cuando el formato del RUT es inválido."""

    def __init__(self, valor_rut: str, formato_esperado: str) -> None:
        super().__init__(
            f"Formato de RUT inválido: '{valor_rut}'. "
            f"Formato esperado: {formato_esperado}",
            codigo_error="CARACTERES_INVALIDOS",
            valor_rut=valor_rut,
            formato_esperado=formato_esperado,
        )


class ErrorDigitoRut(ErrorValidacionRut):
    """Se lanza cuando el dígito verificador es incorrecto."""

    def __init__(self, digito_entregado: str, digito_calculado: str) -> None:
        super().__init__(
            f"Dígito verificador no coincide: se entregó '{digito_entregado}', "
            f"se calculó '{digito_calculado}'",
            codigo_error="DV_DISCORDANTE",
            digito_entregado=digito_entregado,
            digito_calculado=digito_calculado,
        )


class ErrorLongitudRut(ErrorValidacionRut):
    """Se lanza cuando la longitud del RUT es inválida."""

    def __init__(
        self,
        valor_rut: str,
        longitud: int,
        limite: int,
        minimo: bool = False,
    ) -> None:
        if minimo:
            mensaje = (
                f"El RUT '{valor_rut}' es menor a la longitud mínima: "
                f"{longitud} < {limite}"
            )
            contexto = {"longitud_min": limite}
        else:
            mensaje = (
                f"El RUT '{valor_rut}' excede la longitud máxima: {longitud} > {limite}"
            )
            contexto = {"longitud_max": limite}

        super().__init__(
            mensaje,
            codigo_error="LONGITUD_MINIMA" if minimo else "LONGITUD_MAXIMA",
            valor_rut=valor_rut,
            longitud=longitud,
            **contexto,
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
