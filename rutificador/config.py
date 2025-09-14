"""Definiciones de configuración para Rutificador."""
from dataclasses import dataclass
from enum import Enum
from typing import Tuple


@dataclass(frozen=True)
class ConfiguracionRut:
    """Clase de configuración para los parámetros de validación del RUT."""

    factores_verificacion: Tuple[int, ...] = (2, 3, 4, 5, 6, 7)
    modulo: int = 11
    max_digitos: int = 8
    min_digitos: int = 1

    def __post_init__(self) -> None:
        """Valida los parámetros de configuración."""
        if self.modulo <= 0:
            raise ValueError("El módulo debe ser positivo")
        if self.max_digitos <= 0 or self.min_digitos <= 0:
            raise ValueError("Los límites de dígitos deben ser positivos")
        if self.min_digitos > self.max_digitos:
            raise ValueError("El mínimo de dígitos no puede exceder al máximo")


# Instancia de configuración predeterminada
CONFIGURACION_POR_DEFECTO = ConfiguracionRut()


class RigorValidacion(Enum):
    """Enumeración de niveles de rigurosidad de validación."""

    ESTRICTO = "estricto"
    FLEXIBLE = "flexible"
    LEGADO = "legado"


__all__ = [
    "ConfiguracionRut",
    "CONFIGURACION_POR_DEFECTO",
    "RigorValidacion",
]

# Alias para compatibilidad retroactiva
RutConfig = ConfiguracionRut
