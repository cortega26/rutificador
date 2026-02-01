# SECURITY-CRITICAL
import base64
import hashlib
import hmac
import logging
import re
import time
import unicodedata
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Iterator, Literal, Optional, TypedDict, Union

from .config import CONFIGURACION_POR_DEFECTO, ConfiguracionRut, RigorValidacion
from .errores import DetalleError, crear_detalle_error
from .exceptions import ErrorValidacionRut
from .validador import ValidadorRut
from .utils import calcular_digito_verificador, asegurar_booleano

logger = logging.getLogger(__name__)

EstadoValidacion = Literal["incomplete", "possible", "valid", "invalid"]

_BASE_CON_PUNTOS = re.compile(r"^\d{1,3}(?:\.\d{3})*$")


@dataclass(frozen=True)
class ValidacionResultado:
    """Resultado estructurado de una validación incremental."""

    original: str
    normalizado: Optional[str]
    base: Optional[str]
    dv: Optional[str]
    estado: EstadoValidacion
    errores: list[DetalleError]
    advertencias: list[DetalleError]
    validador_modo: str
    duracion: float


@dataclass(frozen=True)
class RutBase:
    """Representación inmutable de la base de un RUT."""

    base: str
    rut_original: str
    validador: ValidadorRut = field(
        default_factory=ValidadorRut, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        if not isinstance(self.rut_original, str):
            raise ErrorValidacionRut(
                "El RUT original debe ser una cadena", error_code="TYPE_ERROR"
            )
        base_validada = self.validador.validar_base(self.base, self.rut_original)
        object.__setattr__(self, "base", base_validada)

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.base


class Rut:
    """Representación de un RUT chileno completo."""

    @staticmethod
    def _agregar_advertencia(
        advertencias: list[DetalleError], vistos: set[str], codigo: str
    ) -> None:
        if codigo in vistos:
            return
        advertencias.append(crear_detalle_error(codigo))
        vistos.add(codigo)

    @staticmethod
    def normalizar(
        valor: Union[str, int],
        *,
        modo: RigorValidacion = RigorValidacion.ESTRICTO,
    ) -> tuple[Optional[str], list[DetalleError], list[DetalleError]]:
        """Normaliza un RUT sin validar su dígito verificador."""

        errores: list[DetalleError] = []
        advertencias: list[DetalleError] = []
        vistos: set[str] = set()

        if not isinstance(valor, (str, int)):
            errores.append(crear_detalle_error("TYPE_ERROR"))
            return None, errores, advertencias

        cadena_original = str(valor)
        cadena = unicodedata.normalize("NFKC", cadena_original)
        cambio_unicode = cadena != cadena_original

        cadena_recortada = cadena.strip()
        if cadena_recortada != cadena:
            Rut._agregar_advertencia(advertencias, vistos, "NORMALIZED_WS")
        cadena = cadena_recortada

        if any(simbolo in cadena for simbolo in ("_", "–", "—")):
            cadena = cadena.replace("_", "-").replace("–", "-").replace("—", "-")
            Rut._agregar_advertencia(advertencias, vistos, "NORMALIZED_DASH")

        if re.search(r"\s", cadena):
            if modo == RigorValidacion.ESTRICTO:
                errores.append(crear_detalle_error("INVALID_CHARS"))
                return None, errores, advertencias
            sin_espacios = re.sub(r"\s+", "", cadena)
            if sin_espacios != cadena:
                Rut._agregar_advertencia(advertencias, vistos, "NORMALIZED_WS")
            cadena = sin_espacios

        if cadena == "":
            errores.append(crear_detalle_error("EMPTY_RUT"))
            return None, errores, advertencias

        if re.search(r"[^0-9kK\.-]", cadena):
            errores.append(crear_detalle_error("INVALID_CHARS"))
            return None, errores, advertencias

        if not re.search(r"\d", cadena):
            return None, errores, advertencias

        if cadena.count("-") > 1:
            errores.append(crear_detalle_error("FORMAT_HYPHEN"))
            return None, errores, advertencias

        guion_presente = "-" in cadena
        base_raw = cadena
        dv_raw: Optional[str] = None
        dv_faltante = False

        if guion_presente:
            base_raw, dv_raw = cadena.split("-", 1)
            if base_raw == "":
                errores.append(crear_detalle_error("FORMAT_HYPHEN"))
                return None, errores, advertencias
            if dv_raw == "":
                dv_faltante = True
                dv_raw = None

        if "." in base_raw:
            if not _BASE_CON_PUNTOS.fullmatch(base_raw):
                errores.append(crear_detalle_error("FORMAT_DOTS"))
                return None, errores, advertencias
            base_sin_puntos = base_raw.replace(".", "")
            Rut._agregar_advertencia(advertencias, vistos, "NORMALIZED_DOTS")
        else:
            base_sin_puntos = base_raw

        base_normalizada = base_sin_puntos.lstrip("0")
        if base_normalizada == "":
            base_normalizada = "0"
        if base_normalizada != base_sin_puntos:
            Rut._agregar_advertencia(advertencias, vistos, "LEADING_ZEROS")

        dv_normalizado: Optional[str] = None
        if dv_raw is not None:
            if len(dv_raw) != 1 or not re.fullmatch(r"[0-9kK]", dv_raw):
                errores.append(crear_detalle_error("DV_INVALID"))
                return None, errores, advertencias
            dv_normalizado = dv_raw.lower()
            if dv_raw != dv_normalizado:
                Rut._agregar_advertencia(advertencias, vistos, "NORMALIZED_DV")

        if cambio_unicode and not (
            "NORMALIZED_WS" in vistos or "NORMALIZED_DASH" in vistos
        ):
            errores.append(crear_detalle_error("INVALID_CHARS"))
            return None, errores, advertencias

        if dv_normalizado is None and dv_faltante:
            normalizado = f"{base_normalizada}-"
        elif dv_normalizado is None:
            normalizado = base_normalizada
        else:
            normalizado = f"{base_normalizada}-{dv_normalizado}"

        return normalizado, errores, advertencias

    @staticmethod
    def parse(
        valor: Union[str, int],
        *,
        modo: RigorValidacion = RigorValidacion.ESTRICTO,
        configuracion: ConfiguracionRut = CONFIGURACION_POR_DEFECTO,
    ) -> ValidacionResultado:
        """Parsea un RUT en forma incremental sin lanzar excepciones."""

        inicio = time.perf_counter()
        try:
            original = str(valor)
        except Exception:  # pragma: no cover - caso extremo
            original = "<valor-no-representable>"

        normalizado, errores, advertencias = Rut.normalizar(valor, modo=modo)
        base: Optional[str] = None
        dv: Optional[str] = None
        estado: EstadoValidacion = "invalid" if errores else "incomplete"

        if errores and all(error.codigo == "EMPTY_RUT" for error in errores):
            estado = "incomplete"

        if not errores:
            if normalizado is None:
                estado = "incomplete"
            else:
                if "-" in normalizado:
                    base, dv_raw = normalizado.split("-", 1)
                    if dv_raw == "":
                        dv = None
                        estado = "possible"
                    else:
                        dv = dv_raw
                else:
                    base = normalizado
                    dv = None

                if base is None or base == "":
                    estado = "incomplete"
                elif len(base) < configuracion.min_digitos:
                    errores.append(crear_detalle_error("LENGTH_MIN"))
                    estado = "invalid"
                elif len(base) > configuracion.max_digitos:
                    errores.append(crear_detalle_error("LENGTH_MAX"))
                    estado = "invalid"
                elif dv is None:
                    estado = "possible"
                else:
                    digito_calculado = calcular_digito_verificador(
                        base, configuracion=configuracion
                    )
                    if dv.lower() != digito_calculado.lower():
                        errores.append(crear_detalle_error("DV_MISMATCH"))
                        estado = "invalid"
                    else:
                        estado = "valid"

        duracion = time.perf_counter() - inicio
        return ValidacionResultado(
            original=original,
            normalizado=normalizado,
            base=base,
            dv=dv,
            estado=estado,
            errores=errores,
            advertencias=advertencias,
            validador_modo=modo.value,
            duracion=duracion,
        )

    @staticmethod
    def mask(
        valor: Union[str, int],
        *,
        keep: int = 4,
        char: str = "*",
        modo: Literal["mask", "token"] = "mask",
        clave: Optional[Union[str, bytes]] = None,
        separador_miles: bool = False,
        mayusculas: bool = False,
        separador_personalizado: str = ".",
    ) -> str:
        """Enmascara o tokeniza un RUT válido."""

        if not isinstance(keep, int) or keep < 0:
            raise ErrorValidacionRut(
                "keep debe ser un entero mayor o igual a 0",
                error_code="TYPE_ERROR",
            )
        if not isinstance(char, str) or len(char) != 1:
            raise ErrorValidacionRut(
                "char debe ser un único carácter",
                error_code="TYPE_ERROR",
            )

        resultado = Rut.parse(valor)
        if (
            resultado.estado != "valid"
            or resultado.base is None
            or resultado.dv is None
        ):
            raise ErrorValidacionRut(
                crear_detalle_error("MASK_STATE").mensaje,
                error_code="MASK_STATE",
            )

        if modo == "token":
            if clave is None:
                raise ErrorValidacionRut(
                    crear_detalle_error("TOKEN_KEY_REQUIRED").mensaje,
                    error_code="TOKEN_KEY_REQUIRED",
                )
            clave_bytes = (
                clave if isinstance(clave, bytes) else str(clave).encode("utf-8")
            )
            mensaje = resultado.normalizado.encode("utf-8")
            digest = hmac.new(clave_bytes, mensaje, hashlib.sha256).digest()
            token = base64.b32encode(digest).decode("ascii").rstrip("=").lower()
            return f"tok_{token}"

        base = resultado.base
        if keep >= len(base):
            base_visible = base
            mascara = ""
        elif keep == 0:
            base_visible = ""
            mascara = char * len(base)
        else:
            base_visible = base[-keep:]
            mascara = char * (len(base) - keep)

        base_mascarada = f"{mascara}{base_visible}"
        if separador_miles:
            base_mascarada = Rut.agregar_separador_miles(
                base_mascarada, separador_personalizado
            )
        rut_mascarado = f"{base_mascarada}-{resultado.dv}"
        if mayusculas:
            rut_mascarado = rut_mascarado.upper()
        return rut_mascarado

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

        self.base = RutBase(self.cadena_base, self.cadena_rut, self.validador)
        self.digito_verificador = calcular_digito_verificador(self.base.base)
        self.validador.validar_digito_verificador(
            digito_ingresado, self.digito_verificador
        )
        logger.debug("RUT validado correctamente")

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
        logger.debug("Inicio de formateo para el RUT")
        try:
            yield
        finally:
            logger.debug("Formateo completado para el RUT")

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
                base_formateada = self.agregar_separador_miles(
                    str(self.base), separador_personalizado
                )
                rut_str = f"{base_formateada}-{self.digito_verificador}"
            if mayusculas:
                rut_str = rut_str.upper()
            logger.debug("RUT formateado correctamente")
            return rut_str

    @staticmethod
    def agregar_separador_miles(numero: str, separador: str = ".") -> str:
        """Expone un separador de miles público para reutilizar desde otros módulos."""
        return Rut._agregar_separador_miles(numero, separador)

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
    def estadisticas_cache(cls) -> "EstadisticasCache":
        info = obtener_rut.cache_info()
        return {"cache_size": info.currsize, "max_cache_size": info.maxsize}


@lru_cache(maxsize=1000)
def obtener_rut(rut: Union[str, int], validador: Optional[ValidadorRut] = None) -> Rut:
    """Obtiene una instancia de :class:`Rut` usando caché LRU."""
    return Rut(rut, validador)


__all__ = [
    "Rut",
    "RutBase",
    "ValidacionResultado",
    "obtener_rut",
    "EstadisticasCache",
]


class EstadisticasCache(TypedDict):
    """Estructura del reporte de caché de :func:`obtener_rut`."""

    cache_size: int
    max_cache_size: Optional[int]
