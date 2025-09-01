"""Utility helpers for Rutificador."""
import logging
import time
from functools import lru_cache, wraps
from typing import Any, Callable

from .config import CONFIGURACION_POR_DEFECTO, RutConfig
from .exceptions import RutValidationError

logger = logging.getLogger(__name__)


def monitor_de_rendimiento(func: Callable) -> Callable:
    """Decorator that measures and logs the performance of a function."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            execution_time = time.perf_counter() - start_time
            logger.debug("%s executed in %.4fs", func.__name__, execution_time)
            return result
        except Exception as exc:  # pragma: no cover - re-raise with logging
            execution_time = time.perf_counter() - start_time
            logger.error("%s failed after %.4fs: %s", func.__name__, execution_time, exc)
            raise

    return wrapper


@lru_cache(maxsize=1024)
@monitor_de_rendimiento
def calcular_digito_verificador(base_numerica: str, config: RutConfig = CONFIGURACION_POR_DEFECTO) -> str:
    """Calculate the verification digit for a given RUT base."""
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
    suma_parcial = sum(
        int(digit) * config.verification_factors[i % len(config.verification_factors)]
        for i, digit in enumerate(reversed(base_numerica))
    )
    digito_verificador = (
        config.modulo - suma_parcial % config.modulo
    ) % config.modulo
    return str(digito_verificador) if digito_verificador < 10 else "k"


def normalizar_base_rut(base: str) -> str:
    """Normalize a RUT base by removing dots and leading zeros."""
    if not isinstance(base, str):
        raise RutValidationError(
            f"Base must be a string, received: {type(base).__name__}",
            error_code="TYPE_ERROR",
        )
    base_normalizada = base.replace(".", "").lstrip("0")
    return base_normalizada if base_normalizada else "0"


__all__ = [
    "monitor_de_rendimiento",
    "calcular_digito_verificador",
    "normalizar_base_rut",
]
