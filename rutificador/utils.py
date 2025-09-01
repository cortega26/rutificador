"""Utility helpers for Rutificador."""

import logging
import time
from functools import lru_cache, wraps
from typing import Any, Callable, TypeVar

from .config import CONFIGURACION_POR_DEFECTO, RutConfig
from .exceptions import RutValidationError

logger = logging.getLogger(__name__)

# Generic type for decorated function return values
R = TypeVar("R")

# Translation table to efficiently remove thousand separators
_PUNTOS_TRADUCCION = str.maketrans("", "", ".")


def monitor_de_rendimiento(func: Callable[..., R]) -> Callable[..., R]:
    """Decorator that measures and logs the performance of a function.

    Args:
        func: Function to wrap.

    Returns:
        Wrapped function preserving the original return type while logging
        execution time.
    """

    @wraps(func)
    def envoltura(*args: Any, **kwargs: Any) -> R:
        tiempo_inicio = time.perf_counter()
        try:
            resultado: R = func(*args, **kwargs)
            tiempo_ejecucion = time.perf_counter() - tiempo_inicio
            logger.debug("%s executed in %.4fs", func.__name__, tiempo_ejecucion)
            return resultado
        except Exception as exc:  # pragma: no cover - re-raise with logging
            tiempo_ejecucion = time.perf_counter() - tiempo_inicio
            logger.error(
                "%s failed after %.4fs: %s", func.__name__, tiempo_ejecucion, exc
            )
            raise

    return envoltura


@lru_cache(maxsize=1024)
@monitor_de_rendimiento
def calcular_digito_verificador(
    base_numerica: str, config: RutConfig = CONFIGURACION_POR_DEFECTO
) -> str:
    """Calculate the verification digit for a given RUT base.

    Args:
        base_numerica: Numeric portion of the RUT as a string without the
            verification digit.
        config: Configuration parameters controlling the calculation.

    Returns:
        The verification digit in lowercase. If the computed digit is 10,
        ``"k"`` is returned.

    Raises:
        RutValidationError: If ``base_numerica`` is not a valid numeric string.
    """
    if not isinstance(base_numerica, str):
        raise RutValidationError(
            f"Numeric base must be a string, received: {type(base_numerica).__name__}",
            error_code="TYPE_ERROR",
        )
    if not base_numerica or not base_numerica.strip():
        raise RutValidationError(
            "Numeric base cannot be empty",
            error_code="EMPTY_BASE",
        )
    base_numerica = base_numerica.strip()
    if not base_numerica.isdigit():
        raise RutValidationError(
            f"Numeric base '{base_numerica}' must contain only digits",
            error_code="INVALID_DIGITS",
        )
    # Use itertools.cycle to avoid costly modulo operations inside the loop
    # and keep the implementation efficient for large bases.
    from itertools import cycle

    factores = cycle(config.verification_factors)
    suma_parcial = sum(int(d) * f for d, f in zip(reversed(base_numerica), factores))
    digito_verificador = (config.modulo - suma_parcial % config.modulo) % config.modulo
    return str(digito_verificador) if digito_verificador < 10 else "k"


def normalizar_base_rut(base: str) -> str:
    """Normalize a RUT base by removing dots and leading zeros."""
    if not isinstance(base, str):
        raise RutValidationError(
            f"Base must be a string, received: {type(base).__name__}",
            error_code="TYPE_ERROR",
        )
    base_normalizada = base.translate(_PUNTOS_TRADUCCION).lstrip("0")
    return base_normalizada if base_normalizada else "0"


__all__ = [
    "monitor_de_rendimiento",
    "calcular_digito_verificador",
    "normalizar_base_rut",
]
