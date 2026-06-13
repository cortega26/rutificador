# SECURITY-CRITICAL
"""Validación de formato y dígito verificador de RUTs.

Proporciona ``ValidadorRut`` con tres modos de rigor (``ESTRICTO``,
``FLEXIBLE``, ``LEGADO``) y el protocolo ``Validador`` para implementar
validadores personalizados.
"""

import logging
import re
import warnings
from typing import Optional, Protocol, runtime_checkable, Match

from .config import CONFIGURACION_POR_DEFECTO, ConfiguracionRut, RigorValidacion
from .exceptions import (
    ErrorFormatoRut,
    ErrorDigitoRut,
    ErrorLongitudRut,
    ErrorValidacionRut,
)
from .utils import (
    RE_BASE_CON_PUNTOS,
    RE_BASE_DIGITOS,
    normalizar_base_rut,
    asegurar_cadena_no_vacia,
    _limpiar_entrada,
)

logger = logging.getLogger(__name__)

# Expresiones regulares compiladas una vez
RUT_REGEX = re.compile(r"^((?:\d{1,3}(?:\.\d{3})*)|\d+)(-([0-9kK]))?$")


@runtime_checkable
class Validador(Protocol):  # pylint: disable=too-few-public-methods
    """Protocolo para validadores de RUT.

    .. deprecated::
        Use :class:`ValidadorRut` en su lugar. ``Validador`` se eliminará en v2.0.
    """

    def validar(self, cadena_rut: str) -> bool:  # pragma: no cover - protocolo
        """Valida una cadena de RUT."""
        warnings.warn(
            "Validador está obsoleto, usa ValidadorRut en su lugar",
            DeprecationWarning,
            stacklevel=2,
        )
        raise NotImplementedError


class ValidadorRut:
    """Validador de RUT con niveles de rigurosidad configurables."""

    def __init__(
        self,
        configuracion: ConfiguracionRut = CONFIGURACION_POR_DEFECTO,
        modo: RigorValidacion = RigorValidacion.ESTRICTO,
    ) -> None:
        """Inicializa el validador con configuración y rigor.

        Args:
            configuracion: Parámetros de validación (factores, módulo,
                dígitos mínimo/máximo).
            modo: Nivel de rigurosidad (``ESTRICTO`` o ``FLEXIBLE``).
                ``LEGADO`` está obsoleto y se eliminará en v2.0; usa
                ``FLEXIBLE`` en su lugar.
        """
        if modo == RigorValidacion.LEGADO:
            warnings.warn(
                "RigorValidacion.LEGADO está obsoleto y se eliminará en v2.0. "
                "Usa RigorValidacion.FLEXIBLE en su lugar.",
                DeprecationWarning,
                stacklevel=2,
            )
        self.configuracion = configuracion
        self.modo = modo
        logger.debug("ValidadorRut inicializado con modo: %s", modo.value)

    def validar_formato(self, cadena_rut: str) -> Match[str]:
        """Valida el formato del RUT."""
        cadena_rut = asegurar_cadena_no_vacia(cadena_rut, "RUT")

        if self.modo == RigorValidacion.FLEXIBLE:
            cadena_rut, _ = _limpiar_entrada(cadena_rut)

        match = RUT_REGEX.fullmatch(cadena_rut)
        if not match:
            raise ErrorFormatoRut(
                cadena_rut,
                (
                    "XXXXXXXX-X o XX.XXX.XXX-X donde X son dígitos "
                    "y el último puede ser 'k'"
                ),
            )

        base_capturada = match.group(1)
        base_normalizada = normalizar_base_rut(base_capturada)
        if len(base_normalizada) > self.configuracion.max_digitos:
            raise ErrorLongitudRut(
                cadena_rut, len(base_normalizada), self.configuracion.max_digitos
            )
        logger.debug("Formato de RUT validado correctamente")
        return match

    def validar_base(self, base: str, rut_original: str) -> str:
        """Valida y normaliza el número base del RUT."""
        base = asegurar_cadena_no_vacia(base, "base")

        if not (RE_BASE_CON_PUNTOS.match(base) or RE_BASE_DIGITOS.match(base)):
            raise ErrorFormatoRut(
                base, "cadena numérica con separadores de miles opcionales"
            )

        base_normalizada = normalizar_base_rut(base)
        if len(base_normalizada) < self.configuracion.min_digitos:
            raise ErrorLongitudRut(
                rut_original,
                len(base_normalizada),
                self.configuracion.min_digitos,
                minimo=True,
            )
        if len(base_normalizada) > self.configuracion.max_digitos:
            raise ErrorLongitudRut(
                rut_original, len(base_normalizada), self.configuracion.max_digitos
            )
        logger.debug("Base validada y normalizada correctamente")
        return base_normalizada

    def validar_digito_verificador(
        self, digito_ingresado: Optional[str], digito_calculado: str
    ) -> None:
        """Valida el dígito verificador del RUT."""
        if digito_ingresado is None:
            return
        if not isinstance(digito_ingresado, str):
            raise ErrorValidacionRut(
                "El dígito verificador debe ser una cadena", codigo_error="ERROR_TIPO"
            )
        if digito_ingresado.lower() != digito_calculado.lower():
            raise ErrorDigitoRut(digito_ingresado, digito_calculado)
        logger.debug(
            "Dígito verificador validado: %s == %s", digito_ingresado, digito_calculado
        )


# Alias para compatibilidad retroactiva
RutValidator = ValidadorRut

_DEPRECATED_ALIASES: dict[str, str] = {
    "RutValidator": "ValidadorRut",
}


def __getattr__(name: str):
    if name in _DEPRECATED_ALIASES:
        warnings.warn(
            f"{name} está obsoleto, usa {_DEPRECATED_ALIASES[name]} en su lugar",
            DeprecationWarning,
            stacklevel=2,
        )
        return globals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "Validador",
    "ValidadorRut",
    "RutValidator",
]
