# SECURITY-CRITICAL
"""Clase principal RUT y lógica de validación.

Define ``Rut``, la clase inmutable que representa un RUT chileno validado,
junto con ``RutBase`` (base numérica) y ``ValidacionResultado`` (resultado
tolerante a fallos). Incluye métodos de formateo, enmascaramiento,
sugerencias y administración de caché.
"""

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
from .utils import (
    RE_BASE_CON_PUNTOS,
    calcular_digito_verificador,
    asegurar_booleano,
    _limpiar_entrada,
)
from .sugestor import sugerir_ruts, mejorar_con_confianza

logger = logging.getLogger(__name__)

EstadoValidacion = Literal["incompleto", "posible", "valido", "invalido"]


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
    def _validar_tipo_entrada(
        valor: Union[str, int],
    ) -> tuple[Optional[str], Optional[str], list[DetalleError], list[DetalleError]]:
        errores: list[DetalleError] = []
        advertencias: list[DetalleError] = []
        if not isinstance(valor, (str, int)):
            errores.append(crear_detalle_error("ERROR_TIPO"))
            return None, None, errores, advertencias
        cadena_original = str(valor)
        cadena, _ = _limpiar_entrada(cadena_original)
        return cadena_original, cadena, errores, advertencias

    @staticmethod
    def _verificar_espacios(
        cadena_original: str,
        modo: RigorValidacion,
        errores: list[DetalleError],
        advertencias: list[DetalleError],
        vistos: set[str],
    ) -> bool:
        if not re.search(r"\s", cadena_original):
            return True
        if modo == RigorValidacion.ESTRICTO:
            errores.append(crear_detalle_error("CARACTERES_INVALIDOS"))
            return False
        Rut._agregar_advertencia(advertencias, vistos, "NORMALIZACION_ESPACIOS")
        return True

    @staticmethod
    def _verificar_guiones_alternativos(
        cadena_original: str,
        advertencias: list[DetalleError],
        vistos: set[str],
    ) -> None:
        if any(simbolo in cadena_original for simbolo in ("_", "–", "—", "−")):
            Rut._agregar_advertencia(advertencias, vistos, "NORMALIZACION_GUION")

    @staticmethod
    def _validar_caracteres_base(
        cadena: str,
        errores: list[DetalleError],
    ) -> bool:
        if cadena == "":
            errores.append(crear_detalle_error("RUT_VACIO"))
            return False
        if re.search(r"[^0-9kK\.-]", cadena):
            errores.append(crear_detalle_error("CARACTERES_INVALIDOS"))
            return False
        if not re.search(r"\d", cadena):
            return False
        if cadena.count("-") > 1:
            errores.append(crear_detalle_error("FORMATO_GUION"))
            return False
        return True

    @staticmethod
    def _separar_base_dv(
        cadena: str,
        errores: list[DetalleError],
    ) -> tuple[Optional[str], Optional[str], bool]:
        if "-" not in cadena:
            return cadena, None, False
        base_raw, dv_raw = cadena.split("-", 1)
        if base_raw == "":
            errores.append(crear_detalle_error("FORMATO_GUION"))
            return None, None, False
        if dv_raw == "":
            return base_raw, None, True
        return base_raw, dv_raw, False

    @staticmethod
    def _normalizar_puntos(
        base_raw: str,
        advertencias: list[DetalleError],
        vistos: set[str],
    ) -> Optional[str]:
        if "." not in base_raw:
            return base_raw
        if not RE_BASE_CON_PUNTOS.fullmatch(base_raw):
            return None
        Rut._agregar_advertencia(advertencias, vistos, "NORMALIZACION_PUNTOS")
        return base_raw.replace(".", "")

    @staticmethod
    def _normalizar_ceros(
        base_sin_puntos: str,
        advertencias: list[DetalleError],
        vistos: set[str],
    ) -> str:
        base_normalizada = base_sin_puntos.lstrip("0")
        if base_normalizada == "":
            base_normalizada = "0"
        if base_normalizada != base_sin_puntos:
            Rut._agregar_advertencia(advertencias, vistos, "CEROS_IZQUIERDA")
        return base_normalizada

    @staticmethod
    def _normalizar_dv(
        dv_raw: Optional[str],
        advertencias: list[DetalleError],
        vistos: set[str],
    ) -> tuple[Optional[str], bool]:
        if dv_raw is None:
            return None, True
        if len(dv_raw) != 1 or not re.fullmatch(r"[0-9kK]", dv_raw):
            return None, False
        dv_normalizado = dv_raw.lower()
        if dv_raw != dv_normalizado:
            Rut._agregar_advertencia(advertencias, vistos, "NORMALIZACION_DV")
        return dv_normalizado, True

    @staticmethod
    def _reconstruir_normalizado(
        base_normalizada: str,
        dv_normalizado: Optional[str],
        dv_faltante: bool,
    ) -> str:
        if dv_normalizado is None and dv_faltante:
            return f"{base_normalizada}-"
        if dv_normalizado is None:
            return base_normalizada
        return f"{base_normalizada}-{dv_normalizado}"

    @staticmethod
    def normalizar(
        valor: Union[str, int],
        *,
        modo: RigorValidacion = RigorValidacion.ESTRICTO,
    ) -> tuple[Optional[str], list[DetalleError], list[DetalleError]]:
        """Normaliza un RUT sin validar su dígito verificador."""

        cadena_original, cadena, errores, advertencias = Rut._validar_tipo_entrada(
            valor
        )
        if cadena is None:
            return None, errores, advertencias

        # Garantizado por _validar_tipo_entrada: si cadena no es None,
        # cadena_original tampoco lo es
        if cadena_original is None:
            return None, errores, advertencias

        vistos: set[str] = set()

        if not Rut._verificar_espacios(
            cadena_original, modo, errores, advertencias, vistos
        ):
            return None, errores, advertencias

        Rut._verificar_guiones_alternativos(cadena_original, advertencias, vistos)

        if not Rut._validar_caracteres_base(cadena, errores):
            return None, errores, advertencias

        base_raw, dv_raw, dv_faltante = Rut._separar_base_dv(cadena, errores)
        if base_raw is None:
            return None, errores, advertencias

        base_sin_puntos = Rut._normalizar_puntos(base_raw, advertencias, vistos)
        if base_sin_puntos is None:
            errores.append(crear_detalle_error("FORMATO_PUNTOS"))
            return None, errores, advertencias

        base_normalizada = Rut._normalizar_ceros(base_sin_puntos, advertencias, vistos)

        dv_normalizado, dv_ok = Rut._normalizar_dv(dv_raw, advertencias, vistos)
        if not dv_ok:
            errores.append(crear_detalle_error("DV_INVALIDO"))
            return None, errores, advertencias

        normalizado = Rut._reconstruir_normalizado(
            base_normalizada, dv_normalizado, dv_faltante
        )
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
            if resultado.normalizado is None:
                raise ErrorValidacionRut(
                    crear_detalle_error("ESTADO_ENMASCARADO").mensaje,
                    codigo_error="ESTADO_ENMASCARADO",
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
        """Construye y valida un RUT.

        Args:
            rut: RUT como cadena (``"12.345.678-5"``) o entero (``12345678``).
                Acepta puntos, guiones y espacios como separadores.
            validador: Validador personalizado. Por defecto usa ``ValidadorRut()``
                en modo ``ESTRICTO``.

        Raises:
            ErrorValidacionRut: Si el RUT no pasa la validación de tipo,
                formato o dígito verificador.
        """
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
        """Formatea el RUT con las opciones especificadas.

        Args:
            separador_miles: Si ``True``, agrega separadores de miles
                (ej: ``12.345.678-5``).
            mayusculas: Si ``True``, la 'k' del DV se muestra en mayúscula.
            separador_personalizado: Carácter usado como separador de miles
                (por defecto ``"."``). Solo se aplica si ``separador_miles``
                es ``True``.

        Returns:
            El RUT formateado como cadena.

        Raises:
            ErrorValidacionRut: Si ``separador_personalizado`` no es un
                único carácter.
        """
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
        """Limpia la caché de la fábrica ``obtener_rut``."""
        obtener_rut.cache_clear()
        logger.info("Caché de RUT limpiada")

    @classmethod
    def estadisticas_cache(cls) -> "EstadisticasCache":
        """Retorna estadísticas de la caché de ``obtener_rut``.

        Returns:
            Diccionario con ``tamanio_cache`` y ``tamanio_max_cache``.
        """
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
