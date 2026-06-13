"""Definiciones de configuración para Rutificador."""

from dataclasses import dataclass
from enum import Enum
from typing import Tuple

from .exceptions import ErrorValidacionRut


@dataclass(frozen=True)
class ConfiguracionRut:
    """Clase de configuración para los parámetros de validación del RUT."""

    factores_verificacion: Tuple[int, ...] = (2, 3, 4, 5, 6, 7)
    modulo: int = 11
    max_digitos: int = 9
    min_digitos: int = 1

    def __post_init__(self) -> None:
        """Valida los parámetros de configuración."""
        if self.modulo <= 0:
            raise ErrorValidacionRut(
                "El módulo debe ser positivo", codigo_error="CONFIGURACION_INVALIDA"
            )
        if self.max_digitos <= 0 or self.min_digitos <= 0:
            raise ErrorValidacionRut(
                "Los límites de dígitos deben ser positivos",
                codigo_error="CONFIGURACION_INVALIDA",
            )
        if self.min_digitos > self.max_digitos:
            raise ErrorValidacionRut(
                "El mínimo de dígitos no puede exceder al máximo",
                codigo_error="CONFIGURACION_INVALIDA",
            )


# Instancia de configuración predeterminada
CONFIGURACION_POR_DEFECTO = ConfiguracionRut()


class RigorValidacion(Enum):
    """Enumeración de niveles de rigurosidad de validación.

    - ``ESTRICTO``: rechaza cualquier variante de formato no canónica
      (espacios internos, guiones alternativos, etc.).
    - ``FLEXIBLE``: normaliza esas variantes y emite advertencias
      ``NORMALIZACION_*``.
    - ``LEGADO``: **obsoleto** — emite ``DeprecationWarning`` y se
      comporta como ``FLEXIBLE``. Se eliminará en v2.0.
    """

    ESTRICTO = "estricto"
    FLEXIBLE = "flexible"
    LEGADO = "legado"  # Deprecated: usar FLEXIBLE


__all__ = [
    "ConfiguracionRut",
    "CONFIGURACION_POR_DEFECTO",
    "RigorValidacion",
]
