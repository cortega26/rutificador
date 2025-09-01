"""Configuration definitions for Rutificador."""
from dataclasses import dataclass
from enum import Enum
from typing import Tuple


@dataclass(frozen=True)
class RutConfig:
    """Configuration class for RUT validation parameters."""

    verification_factors: Tuple[int, ...] = (2, 3, 4, 5, 6, 7)
    modulo: int = 11
    max_digits: int = 8
    min_digits: int = 1

    def __post_init__(self) -> None:
        """Validate configuration parameters."""
        if self.modulo <= 0:
            raise ValueError("Modulo must be positive")
        if self.max_digits <= 0 or self.min_digits <= 0:
            raise ValueError("Digit limits must be positive")
        if self.min_digits > self.max_digits:
            raise ValueError("Min digits cannot exceed max digits")


# Default configuration instance
CONFIGURACION_POR_DEFECTO = RutConfig()


class RigorValidacion(Enum):
    """Enumeration of validation strictness levels."""

    ESTRICTO = "strict"
    FLEXIBLE = "lenient"
    LEGADO = "legacy"


__all__ = [
    "RutConfig",
    "CONFIGURACION_POR_DEFECTO",
    "RigorValidacion",
]
