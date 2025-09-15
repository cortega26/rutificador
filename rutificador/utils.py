"""Funciones utilitarias para Rutificador."""

import logging
import time
from functools import lru_cache, wraps
from itertools import cycle
from typing import Any, Callable, TypeVar

from .config import CONFIGURACION_POR_DEFECTO, ConfiguracionRut
from .exceptions import ErrorValidacionRut

logger = logging.getLogger(__name__)

# Tipo genérico para el valor de retorno de funciones decoradas
R = TypeVar("R")

# Tabla de traducción para eliminar separadores de miles de forma eficiente
_PUNTOS_TRADUCCION = str.maketrans("", "", ".")


def configurar_registro(
    level: int = logging.WARNING,
    formato: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
) -> None:
    """Configura el sistema de registro del módulo."""
    logging.basicConfig(level=level, format=formato, force=True)
    logger.setLevel(level)
    logger.info("Registro configurado al nivel: %s", logging.getLevelName(level))


def asegurar_cadena_no_vacia(valor: Any, nombre: str) -> str:
    """Verifica que ``valor`` sea una cadena no vacía."""
    if not isinstance(valor, str):
        raise ErrorValidacionRut(
            f"{nombre} debe ser una cadena, se recibió: {type(valor).__name__}",
            error_code="TYPE_ERROR",
        )
    valor = valor.strip()
    if not valor:
        raise ErrorValidacionRut(
            f"{nombre} no puede estar vacío", error_code="EMPTY_STRING"
        )
    return valor


def asegurar_booleano(valor: Any, nombre: str) -> bool:
    """Verifica que ``valor`` sea booleano."""
    if not isinstance(valor, bool):
        raise ErrorValidacionRut(
            f"{nombre} debe ser booleano, se recibió: {type(valor).__name__}",
            error_code="TYPE_ERROR",
        )
    return valor


def monitor_de_rendimiento(func: Callable[..., R]) -> Callable[..., R]:
    """Decora una función midiendo y registrando su rendimiento.

    Args:
        func: Función a envolver.

    Returns:
        Función envuelta que preserva el tipo de retorno original mientras
        registra el tiempo de ejecución.
    """

    @wraps(func)
    def envoltura(*args: Any, **kwargs: Any) -> R:
        tiempo_inicio = time.perf_counter()
        try:
            resultado: R = func(*args, **kwargs)
            tiempo_ejecucion = time.perf_counter() - tiempo_inicio
            logger.debug("%s ejecutada en %.4fs", func.__name__, tiempo_ejecucion)
            return resultado
        except Exception as exc:  # pragma: no cover - se relanza con registro
            tiempo_ejecucion = time.perf_counter() - tiempo_inicio
            logger.error(
                "%s falló tras %.4fs: %s", func.__name__, tiempo_ejecucion, exc
            )
            raise

    return envoltura


@lru_cache(maxsize=1024)
@monitor_de_rendimiento
def calcular_digito_verificador(
    base_numerica: str, configuracion: ConfiguracionRut = CONFIGURACION_POR_DEFECTO
) -> str:
    """Calcula el dígito verificador para una base de RUT dada.

    Args:
        base_numerica: Parte numérica del RUT sin el dígito verificador.
        configuracion: Parámetros de configuración que controlan el cálculo.

    Returns:
        El dígito verificador en minúsculas. Si el dígito calculado es 10,
        se retorna ``"k"``.

    Raises:
        ErrorValidacionRut: Si ``base_numerica`` no es una cadena numérica válida.
    """
    if not isinstance(base_numerica, str):
        raise ErrorValidacionRut(
            f"La base numérica debe ser una cadena, se recibió: "
            f"{type(base_numerica).__name__}",
            error_code="TYPE_ERROR",
        )
    if not base_numerica or not base_numerica.strip():
        raise ErrorValidacionRut(
            "La base numérica no puede estar vacía",
            error_code="EMPTY_BASE",
        )
    base_numerica = base_numerica.strip()
    if not base_numerica.isdigit():
        raise ErrorValidacionRut(
            f"La base numérica '{base_numerica}' debe contener solo dígitos",
            error_code="INVALID_DIGITS",
        )
    # Se utiliza itertools.cycle para evitar operaciones costosas de módulo
    # dentro del bucle y mantener eficiente la implementación para bases grandes.

    factores = cycle(configuracion.factores_verificacion)
    suma_parcial = sum(int(d) * f for d, f in zip(reversed(base_numerica), factores))
    digito_verificador = (
        configuracion.modulo - suma_parcial % configuracion.modulo
    ) % configuracion.modulo
    return str(digito_verificador) if digito_verificador < 10 else "k"


def normalizar_base_rut(base: str) -> str:
    """Normaliza una base de RUT eliminando puntos y ceros iniciales."""
    if not isinstance(base, str):
        raise ErrorValidacionRut(
            f"La base debe ser una cadena, se recibió: {type(base).__name__}",
            error_code="TYPE_ERROR",
        )
    base_normalizada = base.translate(_PUNTOS_TRADUCCION).lstrip("0")
    return base_normalizada if base_normalizada else "0"


__all__ = [
    "monitor_de_rendimiento",
    "calcular_digito_verificador",
    "normalizar_base_rut",
    "configurar_registro",
    "asegurar_cadena_no_vacia",
    "asegurar_booleano",
]
