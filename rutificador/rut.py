import logging
from dataclasses import dataclass
from contextlib import contextmanager
from functools import lru_cache
from typing import Any, Dict, Iterator, Optional, Union

from .exceptions import ErrorValidacionRut
from .validador import ValidadorRut
from .utils import calcular_digito_verificador, asegurar_booleano

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RutBase:
    """Representación inmutable de la base de un RUT."""

    base: str
    rut_original: str

    def __post_init__(self) -> None:
        if not isinstance(self.rut_original, str):
            raise ErrorValidacionRut(
                "El RUT original debe ser una cadena", error_code="TYPE_ERROR"
            )
        validador = ValidadorRut()
        base_validada = validador.validar_base(self.base, self.rut_original)
        object.__setattr__(self, "base", base_validada)

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.base


class Rut:
    """Representación de un RUT chileno completo."""

    def __init__(
        self, rut: Union[str, int], validador: Optional[ValidadorRut] = None
    ) -> None:
        if not isinstance(rut, (str, int)):
            raise ErrorValidacionRut(
                f"El RUT debe ser cadena o entero, se recibió: {type(rut).__name__}",
                error_code="TYPE_ERROR",
            )
        self.cadena_rut = str(rut).strip()
        if not self.cadena_rut:
            raise ErrorValidacionRut(
                "El RUT no puede estar vacío", error_code="EMPTY_RUT"
            )
        self.validador = validador or ValidadorRut()
        self._analizar_y_validar()

    def _analizar_y_validar(self) -> None:
        if self.cadena_rut.isdigit():
            self.cadena_base = self.cadena_rut
            digito_ingresado = None
        else:
            match_result = self.validador.validar_formato(self.cadena_rut)
            self.cadena_base = match_result.group(1)
            digito_ingresado = match_result.group(3)

        self.base = RutBase(self.cadena_base, self.cadena_rut)
        self.digito_verificador = calcular_digito_verificador(self.base.base)
        self.validador.validar_digito_verificador(
            digito_ingresado, self.digito_verificador
        )
        logger.debug("RUT validado correctamente: %s", self)

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.base}-{self.digito_verificador}"

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"Rut('{self}')"

    def __eq__(self, other: Any) -> bool:  # pragma: no cover - trivial
        if not isinstance(other, Rut):
            return NotImplemented
        return str(self) == str(other)

    def __hash__(self) -> int:  # pragma: no cover - trivial
        return hash(str(self))

    @contextmanager
    def _contexto_formateo(self) -> Iterator[None]:
        logger.debug("Inicio de formateo para el RUT: %s", self)
        try:
            yield
        finally:
            logger.debug("Formateo completado para el RUT: %s", self)

    def formatear(
        self,
        separador_miles: bool = False,
        mayusculas: bool = False,
        separador_personalizado: str = ".",
    ) -> str:
        asegurar_booleano(separador_miles, "separador_miles")
        asegurar_booleano(mayusculas, "mayusculas")
        if (
            not isinstance(separador_personalizado, str)
            or len(separador_personalizado) != 1
        ):
            raise ErrorValidacionRut(
                "separador_personalizado debe ser un único carácter",
                error_code="FORMAT_ERROR",
            )
        with self._contexto_formateo():
            rut_str = str(self)
            if separador_miles:
                base_formateada = self._agregar_separador_miles(
                    str(self.base), separador_personalizado
                )
                rut_str = f"{base_formateada}-{self.digito_verificador}"
            if mayusculas:
                rut_str = rut_str.upper()
            logger.debug("RUT formateado: %s", rut_str)
            return rut_str

    @staticmethod
    def _agregar_separador_miles(numero: str, separador: str = ".") -> str:
        if len(numero) <= 3:
            return numero
        invertido = numero[::-1]
        grupos = [
            invertido[slice(inicio, inicio + 3)]
            for inicio in range(0, len(invertido), 3)
        ]
        formateado = separador.join(grupos)
        return formateado[::-1]

    @classmethod
    def limpiar_cache(cls) -> None:
        obtener_rut.cache_clear()
        logger.info("Caché de RUT limpiada")

    @classmethod
    def estadisticas_cache(cls) -> Dict[str, int]:
        info = obtener_rut.cache_info()
        return {"cache_size": info.currsize, "max_cache_size": info.maxsize}


@lru_cache(maxsize=1000)
def obtener_rut(rut: Union[str, int], validador: Optional[ValidadorRut] = None) -> Rut:
    """Obtiene una instancia de :class:`Rut` usando caché LRU."""
    return Rut(rut, validador)


__all__ = ["Rut", "RutBase", "obtener_rut"]
