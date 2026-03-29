# SECURITY-CRITICAL
import base64
import hashlib
import hmac
import logging
import re
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Iterator, Literal, Optional, TypedDict, Union

from .config import CONFIGURACION_POR_DEFECTO, ConfiguracionRut, RigorValidacion
from .errores import DetalleError, crear_detalle_error
from .exceptions import ErrorValidacionRut
from .validador import ValidadorRut
from .utils import calcular_digito_verificador, asegurar_booleano, _limpiar_entrada
from .sugestor import sugerir_ruts, mejorar_con_confianza

logger = logging.getLogger(__name__)

EstadoValidacion = Literal["incompleto", "posible", "valido", "invalido"]

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
                "El RUT original debe ser una cadena", codigo_error="ERROR_TIPO"
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
            errores.append(crear_detalle_error("ERROR_TIPO"))
            return None, errores, advertencias

        cadena_original = str(valor)
        cadena, _ = _limpiar_entrada(cadena_original)

        if re.search(r"\s", cadena_original):
            if modo == RigorValidacion.ESTRICTO:
                errores.append(crear_detalle_error("CARACTERES_INVALIDOS"))
                return None, errores, advertencias
            Rut._agregar_advertencia(advertencias, vistos, "NORMALIZACION_ESPACIOS")

        if any(simbolo in cadena_original for simbolo in ("_", "–", "—", "−")):
            Rut._agregar_advertencia(advertencias, vistos, "NORMALIZACION_GUION")

        if cadena == "":
            errores.append(crear_detalle_error("RUT_VACIO"))
            return None, errores, advertencias

        if re.search(r"[^0-9kK\.-]", cadena):
            errores.append(crear_detalle_error("CARACTERES_INVALIDOS"))
            return None, errores, advertencias

        if not re.search(r"\d", cadena):
            return None, errores, advertencias

        if cadena.count("-") > 1:
            errores.append(crear_detalle_error("FORMATO_GUION"))
            return None, errores, advertencias

        guion_presente = "-" in cadena
        base_raw = cadena
        dv_raw: Optional[str] = None
        dv_faltante = False

        if guion_presente:
            base_raw, dv_raw = cadena.split("-", 1)
            if base_raw == "":
                errores.append(crear_detalle_error("FORMATO_GUION"))
                return None, errores, advertencias
            if dv_raw == "":
                dv_faltante = True
                dv_raw = None

        if "." in base_raw:
            if not _BASE_CON_PUNTOS.fullmatch(base_raw):
                errores.append(crear_detalle_error("FORMATO_PUNTOS"))
                return None, errores, advertencias
            base_sin_puntos = base_raw.replace(".", "")
            Rut._agregar_advertencia(advertencias, vistos, "NORMALIZACION_PUNTOS")
        else:
            base_sin_puntos = base_raw

        base_normalizada = base_sin_puntos.lstrip("0")
        if base_normalizada == "":
            base_normalizada = "0"
        if base_normalizada != base_sin_puntos:
            Rut._agregar_advertencia(advertencias, vistos, "CEROS_IZQUIERDA")

        dv_normalizado: Optional[str] = None
        if dv_raw is not None:
            if len(dv_raw) != 1 or not re.fullmatch(r"[0-9kK]", dv_raw):
                errores.append(crear_detalle_error("DV_INVALIDO"))
                return None, errores, advertencias
            dv_normalizado = dv_raw.lower()
            if dv_raw != dv_normalizado:
                Rut._agregar_advertencia(advertencias, vistos, "NORMALIZACION_DV")

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
        estado: EstadoValidacion = "invalido" if errores else "incompleto"

        if errores and all(error.codigo == "RUT_VACIO" for error in errores):
            estado = "incompleto"

        if not errores:
            if normalizado is None:
                estado = "incompleto"
            else:
                if "-" in normalizado:
                    base, dv_raw = normalizado.split("-", 1)
                    if dv_raw == "":
                        dv = None
                        estado = "posible"
                    else:
                        dv = dv_raw
                        estado = "posible"
                else:
                    base = normalizado
                    dv = None
                    estado = "posible"

                if base is None or base == "":
                    estado = "incompleto"
                elif len(base) < configuracion.min_digitos:
                    errores.append(crear_detalle_error("LONGITUD_MINIMA"))
                    estado = "invalido"
                elif len(base) > configuracion.max_digitos:
                    errores.append(crear_detalle_error("LONGITUD_MAXIMA"))
                    estado = "invalido"
                elif dv is None:
                    estado = "posible"
                else:
                    digito_calculado = calcular_digito_verificador(
                        base, configuracion=configuracion
                    )
                    if dv.lower() != digito_calculado.lower():
                        errores.append(crear_detalle_error("DV_DISCORDANTE"))
                        estado = "invalido"
                    else:
                        estado = "valido"

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
    def enmascarar(
        valor: Union[str, int],
        *,
        mantener: int = 4,
        caracter: str = "*",
        modo: Literal["mascarada", "token"] = "mascarada",
        clave: Optional[Union[str, bytes]] = None,
        separador_miles: bool = False,
        mayusculas: bool = False,
        separador_personalizado: str = ".",
    ) -> str:
        """Enmascara o tokeniza un RUT válido."""

        if not isinstance(mantener, int) or mantener < 0:
            raise ErrorValidacionRut(
                "mantener debe ser un entero mayor o igual a 0",
                codigo_error="ERROR_TIPO",
            )
        if not isinstance(caracter, str) or len(caracter) != 1:
            raise ErrorValidacionRut(
                "caracter debe ser un único carácter",
                codigo_error="ERROR_TIPO",
            )

        resultado = Rut.parse(valor)
        if (
            resultado.estado != "valido"
            or resultado.base is None
            or resultado.dv is None
        ):
            raise ErrorValidacionRut(
                crear_detalle_error("ESTADO_ENMASCARADO").mensaje,
                codigo_error="ESTADO_ENMASCARADO",
            )

        if modo == "token":
            if clave is None:
                raise ErrorValidacionRut(
                    crear_detalle_error("CLAVE_TOKEN_REQUERIDA").mensaje,
                    codigo_error="CLAVE_TOKEN_REQUERIDA",
                )
            clave_bytes = (
                clave if isinstance(clave, bytes) else str(clave).encode("utf-8")
            )
            mensaje = resultado.normalizado.encode("utf-8")
            digest = hmac.new(clave_bytes, mensaje, hashlib.sha256).digest()
            token = base64.b32encode(digest).decode("ascii").rstrip("=").lower()
            return f"tok_{token}"

        base = resultado.base
        if mantener >= len(base):
            base_visible = base
            mascara = ""
        elif mantener == 0:
            base_visible = ""
            mascara = caracter * len(base)
        else:
            base_visible = base[-mantener:]
            mascara = caracter * (len(base) - mantener)

        base_mascarada = f"{mascara}{base_visible}"
        if separador_miles:
            base_mascarada = Rut.agregar_separador_miles(
                base_mascarada, separador_personalizado
            )
        rut_mascarado = f"{base_mascarada}-{resultado.dv}"
        if mayusculas:
            rut_mascarado = rut_mascarado.upper()
        return rut_mascarado

    # Alias para compatibilidad
    mask = enmascarar

    def __init__(
        self, rut: Union[str, int], validador: Optional[ValidadorRut] = None
    ) -> None:
        if not isinstance(rut, (str, int)):
            raise ErrorValidacionRut(
                f"El RUT debe ser cadena o entero, se recibió: {type(rut).__name__}",
                codigo_error="ERROR_TIPO",
            )
        # Normalizar entrada antes de validar
        self.cadena_rut, _ = _limpiar_entrada(str(rut).strip())
        if not self.cadena_rut:
            raise ErrorValidacionRut(
                "El RUT no puede estar vacío", codigo_error="RUT_VACIO"
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
        return "Rut(base='********', dv='*')"

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
                codigo_error="ERROR_FORMATO",
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

    @staticmethod
    def sugerir(valor: str) -> list[str]:
        """Sugiere RUTs válidos cercanos a la entrada.

        Útil para capturar errores de digitación o 'Did you mean?' en interfaces.
        """
        return sugerir_ruts(valor)

    @staticmethod
    def mejorar(valor: str) -> Optional[str]:
        """Intenta mejorar/corregir un RUT de forma segura.

        Solo una sugerencia inequívoca (distancia 1 y sin ambigüedad) será devuelta.
        """
        return mejorar_con_confianza(valor)

    @classmethod
    def limpiar_cache(cls) -> None:
        obtener_rut.cache_clear()
        logger.info("Caché de RUT limpiada")

    @classmethod
    def estadisticas_cache(cls) -> "EstadisticasCache":
        info = obtener_rut.cache_info()
        return {"tamanio_cache": info.currsize, "tamanio_max_cache": info.maxsize}


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

    tamanio_cache: int
    tamanio_max_cache: Optional[int]
