"""
Módulo principal de Rutificador con mejores prácticas.

Este módulo ofrece una implementación robusta y de alto rendimiento para la
validación y formateo del RUT chileno, con manejo exhaustivo de errores,
registro de eventos y opciones de extensión.
"""

# pylint: disable=too-many-lines

import logging
import re
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import (
    Any,
    Dict,
    List,
    Literal,
    Optional,
    Protocol,
    Sequence,
    Tuple,
    Union,
    runtime_checkable,
    Iterator,
)
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import random
import threading

from .formatter import (
    FormateadorRut,
    FormateadorCSV,
    FormateadorXML,
    FormateadorJSON,
    FabricaFormateadorRut,
)
from .config import CONFIGURACION_POR_DEFECTO, ConfiguracionRut, RigorValidacion
from .exceptions import (
    ErrorRut,
    ErrorValidacionRut,
    ErrorFormatoRut,
    ErrorDigitoRut,
    ErrorLongitudRut,
    ErrorProcesamientoRut,
    RutInvalidoError,
)
from .utils import (
    monitor_de_rendimiento,
    calcular_digito_verificador,
    normalizar_base_rut,
)


# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

logger = logging.getLogger(__name__)


def configurar_registro_basico(level: int = logging.WARNING) -> None:
    """Configura el registro para el módulo rutificador."""
    logging.basicConfig(
        level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


# ============================================================================
# CONFIGURATION AND CONSTANTS
# ============================================================================

# Regex patterns - compiled once for performance
RUT_REGEX = re.compile(r"^(\d{1,8}(?:\.\d{3})*)(-([0-9kK]))?$")
BASE_WITH_DOTS_REGEX = re.compile(r"^\d{1,3}(?:\.\d{3})*$")
BASE_DIGITS_ONLY_REGEX = re.compile(r"^\d+$")

# Definiciones de tipo
FormatoOutput = Literal["csv", "xml", "json"]
ModoValidacion = Literal["estricto", "flexible", "legado"]


# ============================================================================
# ENHANCED VALIDATION LAYER
# ============================================================================


@runtime_checkable
class Validador(Protocol):  # pylint: disable=too-few-public-methods
    """Protocolo para validadores de RUT."""

    def validate(self, cadena_rut: str) -> bool:
        """Valida una cadena de RUT."""
        pass


class ValidadorRut:
    """Validador de RUT con niveles de rigurosidad configurables."""

    def __init__(
        self,
        configuracion: ConfiguracionRut = CONFIGURACION_POR_DEFECTO,
        modo: RigorValidacion = RigorValidacion.ESTRICTO,
    ) -> None:
        """Inicializa el validador con la configuración y el modo de rigurosidad.

        Args:
            configuracion: Parámetros de validación del RUT.
            modo: Nivel de rigurosidad para la validación.
        """
        self.configuracion = configuracion
        self.modo = modo
        logger.debug("ValidadorRut inicializado con modo: %s", modo.value)

    def validar_formato(self, cadena_rut: str) -> re.Match[str]:
        """Valida el formato del RUT con informes detallados de error.

        Args:
            cadena_rut: Cadena de RUT a validar.

        Returns:
            Objeto ``Match`` que contiene los componentes analizados del RUT.

        Raises:
            ErrorFormatoRut: Si el formato es inválido.

        Examples:
            >>> validador = ValidadorRut()
            >>> match = validador.validar_formato("12345678-5")
            >>> match.group(1)  # Número base
            '12345678'
            >>> match.group(3)  # Dígito verificador
            '5'
        """
        if not isinstance(cadena_rut, str):
            raise ErrorFormatoRut(
                str(cadena_rut), "cadena con formato 'XXXXXXXX-X' o 'XX.XXX.XXX-X'"
            )

        if not cadena_rut or not cadena_rut.strip():
            raise ErrorFormatoRut("", "cadena no vacía")

        cadena_rut = cadena_rut.strip()

        if self.modo == RigorValidacion.FLEXIBLE:
            cadena_rut = self._normalizar_entrada(cadena_rut)

        match = RUT_REGEX.fullmatch(cadena_rut)
        if not match:
            raise ErrorFormatoRut(
                cadena_rut,
                "XXXXXXXX-X o XX.XXX.XXX-X donde X son dígitos y el último puede ser 'k'",
            )

        logger.debug("Formato de RUT validado correctamente: %s", cadena_rut)
        return match

    def validar_base(self, base: str, rut_original: str) -> str:
        """Valida y normaliza el número base del RUT con verificaciones adicionales.

        Args:
            base: Número base del RUT.
            rut_original: Cadena original del RUT para contexto de error.

        Returns:
            Número base normalizado.

        Raises:
            ErrorFormatoRut: Si el formato de la base es inválido.
            ErrorLongitudRut: Si la longitud excede los límites.
        """
        if not isinstance(base, str):
            raise ErrorFormatoRut(base, "cadena numérica")

        if not base or not base.strip():
            raise ErrorFormatoRut("", "cadena numérica no vacía")

        base = base.strip()

        if not (BASE_WITH_DOTS_REGEX.match(base) or BASE_DIGITS_ONLY_REGEX.match(base)):
            raise ErrorFormatoRut(
                base, "cadena numérica con separadores de miles opcionales"
            )

        base_normalizada = normalizar_base_rut(base)

        if len(base_normalizada) > self.configuracion.max_digitos:
            raise ErrorLongitudRut(
                rut_original, len(base_normalizada), self.configuracion.max_digitos
            )

        logger.debug("Base validada y normalizada: %s -> %s", base, base_normalizada)
        return base_normalizada

    def validar_digito_verificador(
        self, digito_ingresado: Optional[str], digito_calculado: str
    ) -> None:
        """Valida el dígito verificador con comparación insensible a mayúsculas.

        Args:
            digito_ingresado: Dígito verificador proporcionado por el usuario.
            digito_calculado: Dígito verificador calculado.

        Raises:
            ErrorDigitoRut: Si los dígitos no coinciden.
        """
        if digito_ingresado is not None:
            if not isinstance(digito_ingresado, str):
                raise ErrorFormatoRut(
                    str(digito_ingresado), "carácter único (0-9 o k/K)"
                )

            if digito_ingresado.lower() != digito_calculado.lower():
                raise ErrorDigitoRut(digito_ingresado, digito_calculado)

        logger.debug(
            "Dígito verificador validado: %s == %s", digito_ingresado, digito_calculado
        )

    def _normalizar_entrada(self, cadena_rut: str) -> str:
        """Normaliza la entrada en modo de validación flexible."""
        normalizado = re.sub(r"\s+", "", cadena_rut)
        normalizado = normalizado.replace("_", "-").replace(
            "–", "-"
        )
        return normalizado


# Alias para compatibilidad retroactiva
RutValidator = ValidadorRut


# ============================================================================
# ENHANCED FORMATTING LAYER
# ============================================================================


# ============================================================================
# ENHANCED DOMAIN MODELS
# ============================================================================


@dataclass(frozen=True)
class RutBase:
    """Representación inmutable de la base de un RUT."""

    base: str
    rut_original: str

    def __post_init__(self) -> None:
        """Valida la base después de la inicialización."""
        if not isinstance(self.rut_original, str):
            raise ErrorValidacionRut(
                f"El RUT original debe ser una cadena, se recibió: {type(self.rut_original).__name__}",
                error_code="TYPE_ERROR",
            )

        validador = ValidadorRut()
        base_validada = validador.validar_base(self.base, self.rut_original)

        object.__setattr__(self, "base", base_validada)

    def __str__(self) -> str:
        return self.base


class Rut:
    """Representación mejorada de un RUT chileno completo."""

    # Class-level cache for commonly used RUTs
    _instance_cache: Dict[str, "Rut"] = {}
    _cache_lock = None  # Will be initialized when needed

    def __init__(
        self,
        rut: Union[str, int],
        validador: Optional[ValidadorRut] = None,
        habilitar_cache: bool = True,
    ) -> None:
        """Inicializa una instancia de RUT con validación mejorada.

        Args:
            rut: Valor del RUT como cadena o entero.
            validador: Instancia personalizada de validador.
            habilitar_cache: Si se utiliza caché de instancias.

        Raises:
            ErrorValidacionRut: Si el RUT es inválido.

        Examples:
            >>> rut = Rut("12345678-5")
            >>> str(rut)
            '12345678-5'
            >>> rut = Rut(12345678)  # Sin dígito verificador
            >>> str(rut)
            '12345678-5'
        """
        if Rut._cache_lock is None:
            Rut._cache_lock = threading.RLock()

        if not isinstance(rut, (str, int)):
            raise ErrorValidacionRut(
                f"El RUT debe ser cadena o entero, se recibió: {type(rut).__name__}",
                error_code="TYPE_ERROR",
            )

        self.cadena_rut = str(rut).strip()

        if not self.cadena_rut:
            raise ErrorValidacionRut("El RUT no puede estar vacío", error_code="EMPTY_RUT")

        if habilitar_cache and self.cadena_rut in Rut._instance_cache:
            cached_instance = Rut._instance_cache[self.cadena_rut]
            self.__dict__.update(cached_instance.__dict__)
            logger.debug("RUT recuperado desde la caché: %s", self.cadena_rut)
            return

        self.validador = validador or ValidadorRut()

        self._analizar_y_validar()

        if habilitar_cache and Rut._cache_lock is not None:
            with Rut._cache_lock:
                if len(Rut._instance_cache) < 1000:
                    Rut._instance_cache[self.cadena_rut] = self
                    logger.debug("Instancia de RUT almacenada en caché: %s", self.cadena_rut)

    def _analizar_y_validar(self) -> None:
        """Analiza y valida los componentes del RUT."""
        # Maneja la entrada numérica (sin dígito verificador)
        if self.cadena_rut.isdigit():
            self.cadena_base = self.cadena_rut
            digito_ingresado = None
            logger.debug("Procesando RUT numérico: %s", self.cadena_rut)
        else:
            # Valida el formato y extrae los componentes
            match_result = self.validador.validar_formato(self.cadena_rut)
            self.cadena_base = match_result.group(1)
            digito_ingresado = match_result.group(3)

        # Crea la base y calcula el dígito verificador
        self.base = RutBase(self.cadena_base, self.cadena_rut)
        self.digito_verificador = calcular_digito_verificador(self.base.base)

        # Valida el dígito verificador si se proporcionó
        self.validador.validar_digito_verificador(digito_ingresado, self.digito_verificador)

        logger.debug("RUT successfully validated: %s", self)

    def __str__(self) -> str:
        """Representación en cadena del RUT."""
        return f"{self.base}-{self.digito_verificador}"

    def __repr__(self) -> str:
        """Representación para desarrolladores."""
        return f"Rut('{self}')"

    def __eq__(self, other: Any) -> bool:
        """Comparación de igualdad mejorada."""
        if not isinstance(other, Rut):
            return NotImplemented
        return str(self) == str(other)

    def __hash__(self) -> int:
        """Implementación de hash para usar en conjuntos y diccionarios."""
        return hash(str(self))

    def __lt__(self, other: "Rut") -> bool:
        """Comparación menor a para ordenar."""
        if not isinstance(other, Rut):
            return NotImplemented
        return int(self.base.base) < int(other.base.base)

    @contextmanager
    def _contexto_formateo(self) -> Iterator[None]:
        """Contexto para operaciones de formateo."""
        logger.debug("Inicio de formateo para el RUT: %s", self)
        try:
            yield
        except Exception as e:
            logger.error("El formateo falló para el RUT %s: %s", self, e)
            raise
        finally:
            logger.debug("Formateo completado para el RUT: %s", self)

    def formatear(
        self,
        separador_miles: bool = False,
        mayusculas: bool = False,
        separador_personalizado: str = ".",
    ) -> str:
        """
        Formatea el RUT con diversas opciones de presentación.

        Args:
            separador_miles: Indica si se agregan separadores de miles.
            mayusculas: Indica si el RUT se convierte a mayúsculas.
            separador_personalizado: Carácter para separar los miles.

        Returns:
            Cadena con el RUT formateado.

        Raises:
            ValueError: Si los parámetros no son válidos.

        Examples:
            >>> rut = Rut("12345678-5")
            >>> rut.formatear(separador_miles=True)
            '12.345.678-5'
            >>> rut.formatear(mayusculas=True, custom_separator=",")
            '12345678-5'  # No hay 'k' para convertir
        """
        # Enhanced parameter validation
        if not isinstance(separador_miles, bool):
            raise ValueError(
                f"separador_miles must be bool, received: {type(separador_miles).__name__}"
            )

        if not isinstance(mayusculas, bool):
            raise ValueError(
                f"mayusculas must be bool, received: {type(mayusculas).__name__}"
            )

        if not isinstance(separador_personalizado, str) or len(separador_personalizado) != 1:
            raise ValueError("separador_personalizado debe ser un único carácter")

        with self._contexto_formateo():
            rut_str = str(self)

            if separador_miles:
                base_formateada = self._agregar_separador_miles(
                    str(self.base), separador_personalizado
                )
                rut_str = f"{base_formateada}-{self.digito_verificador}"

            if mayusculas:
                rut_str = rut_str.upper()

            logger.debug("Formatted RUT: %s -> %s", self, rut_str)
            return rut_str

    @staticmethod
    def _agregar_separador_miles(numero: str, separador: str = ".") -> str:
        """
        Agrega separadores de miles con manejo de errores.

        Args:
            numero: Cadena numérica a formatear.
            separador: Carácter separador a utilizar.

        Returns:
            Cadena numérica formateada.

        Raises:
            ErrorValidacionRut: Si el número no puede formatearse.
        """
        try:
            # Usa manipulación de cadenas para mejor rendimiento en cadenas numéricas conocidas
            if len(numero) <= 3:
                return numero

            # Formatea de derecha a izquierda
            reversed_digits = numero[::-1]
            chunks = [
                reversed_digits[i : i + 3] for i in range(0, len(reversed_digits), 3)
            ]
            formateado = separador.join(chunks)
            return formateado[::-1]

        except (ValueError, TypeError) as e:
            raise ErrorValidacionRut(
                f"Error al formatear el número '{numero}': {e}", error_code="FORMAT_ERROR"
            ) from e

    @classmethod
    def limpiar_cache(cls) -> None:
        """Limpia la caché de instancias."""
        if cls._cache_lock is not None:
            with cls._cache_lock:
                cls._instance_cache.clear()
            logger.info("RUT instance cache cleared")

    @classmethod
    def estadisticas_cache(cls) -> Dict[str, int]:
        """Obtiene estadísticas de la caché."""
        if cls._cache_lock is not None:
            with cls._cache_lock:
                return {"cache_size": len(cls._instance_cache), "max_cache_size": 1000}
        return {"cache_size": 0, "max_cache_size": 1000}


# ============================================================================
# ADVANCED BATCH PROCESSING SERVICE
# ============================================================================


@dataclass
class ResultadoLote:
    """Contenedor de resultados para operaciones por lotes."""

    ruts_validos: List[str] = field(default_factory=list)
    ruts_invalidos: List[Tuple[str, str]] = field(default_factory=list)
    tiempo_procesamiento: float = 0.0
    total_procesados: int = 0

    @property
    def tasa_exito(self) -> float:
        """Calcula la tasa de éxito como porcentaje."""
        if self.total_procesados == 0:
            return 0.0
        return (len(self.ruts_validos) / self.total_procesados) * 100


class ProcesadorLotesRut:
    """
    Servicio avanzado para procesar RUTs en lotes con capacidad paralela.

    Este servicio ofrece procesamiento de alto rendimiento de RUTs,
    soporte para ejecución paralela y manejo de errores integral.
    """

    def __init__(
        self,
        validador: Optional[ValidadorRut] = None,
        max_trabajadores: Optional[int] = None,
        tamano_bloque: int = 1000,
    ) -> None:
        """
        Inicializa el procesador de lotes con la configuración indicada.

        Args:
            validador: Instancia de validador personalizada.
            max_trabajadores: Número máximo de hilos de trabajo.
            tamano_bloque: Tamaño de cada bloque para la ejecución paralela.
        """
        self.validador = validador or ValidadorRut()
        self.max_trabajadores = max_trabajadores
        self.tamano_bloque = tamano_bloque
        logger.info(
            "Procesador de lotes inicializado con tamano_bloque=%d",
            tamano_bloque,
        )

    @monitor_de_rendimiento
    def validar_lista_ruts(
        self, ruts: Sequence[str], parallel: bool = True
    ) -> ResultadoLote:
        """
        Validate a list of RUTs with optional parallel processing.

        Args:
            ruts: Sequence of RUT strings to validate.
            parallel: Whether to use parallel processing.

        Returns:
            ResultadoLote con los resultados y estadísticas de validación.

        Raises:
            RutProcessingError: If batch processing fails.
        """
        start_time = time.perf_counter()

        try:
            if not isinstance(ruts, (list, tuple)):
                raise ErrorProcesamientoRut(
                    f"Se esperaba una secuencia, se recibió {type(ruts).__name__}",
                    error_code="TYPE_ERROR",
                )

            if not ruts:
                logger.warning("Se proporcionó una secuencia vacía de RUTs para validar")
                return ResultadoLote(
                    tiempo_procesamiento=time.perf_counter() - start_time
                )

            if parallel and len(ruts) > self.tamano_bloque:
                result = self._validar_paralelo(ruts)
            else:
                result = self._validar_secuencial(ruts)

            result.tiempo_procesamiento = time.perf_counter() - start_time
            result.total_procesados = len(ruts)

            logger.info(
                "Validación por lotes completada: %d válidos, %d inválidos, tasa de éxito: %.1f%%",
                len(result.ruts_validos),
                len(result.ruts_invalidos),
                result.tasa_exito,
            )

            return result

        except Exception as e:
            processing_time = time.perf_counter() - start_time
            logger.error(
                "La validación por lotes falló tras %.4fs: %s", processing_time, e
            )
            raise ErrorProcesamientoRut(
                f"Error en validación por lotes: {e}", error_code="BATCH_ERROR"
            ) from e

    def _validar_secuencial(self, ruts: Sequence[str]) -> ResultadoLote:
        """Validación secuencial de RUTs."""
        result = ResultadoLote()

        for cadena_rut in ruts:
            try:
                rut_obj = Rut(str(cadena_rut), validador=self.validador)
                result.ruts_validos.append(str(rut_obj))
            except (ErrorRut, ValueError, TypeError) as e:
                result.ruts_invalidos.append((str(cadena_rut), str(e)))

        return result

    def _validar_paralelo(self, ruts: Sequence[str]) -> ResultadoLote:
        """Validación paralela de RUTs usando ThreadPoolExecutor."""
        result = ResultadoLote()

        # Submit chunks lazily to avoid constructing an intermediate list of
        # slices which can be expensive for very large inputs.
        with ThreadPoolExecutor(max_workers=self.max_trabajadores) as executor:
            future_to_chunk = {}
            for i in range(0, len(ruts), self.tamano_bloque):
                chunk = ruts[i : i + self.tamano_bloque]
                future_to_chunk[executor.submit(self._validar_bloque, chunk)] = chunk

            for future in as_completed(future_to_chunk):
                try:
                    chunk_result = future.result()
                    result.ruts_validos.extend(chunk_result.ruts_validos)
                    result.ruts_invalidos.extend(chunk_result.ruts_invalidos)
                except Exception as e:
                    chunk = future_to_chunk[future]
                    logger.error("El procesamiento del bloque falló: %s", e)
                    for cadena_rut in chunk:
                        result.ruts_invalidos.append(
                            (str(cadena_rut), f"Error de procesamiento: {e}")
                        )

        return result

    def _validar_bloque(self, chunk: Sequence[str]) -> ResultadoLote:
        """Valida un bloque de RUTs."""
        return self._validar_secuencial(chunk)

    @monitor_de_rendimiento
    def formatear_lista_ruts(
        self,
        ruts: Sequence[str],
        separador_miles: bool = False,
        mayusculas: bool = False,
        formato: Optional[FormatoOutput] = None,
        parallel: bool = True,
        **formatter_kwargs: Any,
    ) -> str:
        """Formatea una lista de RUTs con opciones avanzadas y procesamiento paralelo.

        Args:
            ruts: Secuencia de RUTs a formatear.
            separador_miles: Si se agregan separadores de miles.
            mayusculas: Si los RUTs se convierten a mayúsculas.
            formato: Formato de salida (csv, json, xml, None).
            parallel: Si se utiliza procesamiento en paralelo.
            **formatter_kwargs: Argumentos adicionales para los formateadores.

        Returns:
            Cadena formateada con los RUTs válidos e inválidos.

        Raises:
            ValueError: Si los parámetros son inválidos.
            ErrorProcesamientoRut: Si el procesamiento por lotes falla.
        """
        # Enhanced input validation
        if not isinstance(ruts, (list, tuple)):
            raise ValueError(
                f"ruts debe ser una secuencia, se recibió: {type(ruts).__name__}"
            )

        if not isinstance(separador_miles, bool):
            raise ValueError(
                "separador_miles debe ser bool, se recibió: %s",
                type(separador_miles).__name__,
            )

        if not isinstance(mayusculas, bool):
            raise ValueError(
                "mayusculas debe ser bool, se recibió: %s",
                type(mayusculas).__name__,
            )

        # Validate RUTs
        resultado_validacion = self.validar_lista_ruts(ruts, parallel=parallel)
        ruts_validos = resultado_validacion.ruts_validos
        ruts_invalidos = resultado_validacion.ruts_invalidos

        resultado_parts = []

        # Process valid RUTs
        if ruts_validos:
            ruts_validos_formateados = []
            for cadena_rut in ruts_validos:
                try:
                    rut_obj = Rut(cadena_rut, validador=self.validador)
                    rut_formateado = rut_obj.formatear(
                        separador_miles=separador_miles, mayusculas=mayusculas
                    )
                    ruts_validos_formateados.append(rut_formateado)
                except (ErrorRut, ValueError, TypeError) as e:
                    logger.warning(
                        "El formateo falló para el RUT válido %s: %s", cadena_rut, e
                    )
                    continue

            resultado_parts.append("RUTs válidos:")

            # Apply specific format if requested
            if formato:
                formatter = FabricaFormateadorRut.obtener_formateador(
                    formato, **formatter_kwargs
                )
                if formatter:
                    resultado_parts.append(
                        formatter.formatear(ruts_validos_formateados)
                    )
                else:
                    available_formats = (
                        FabricaFormateadorRut.obtener_formatos_disponibles()
                    )
                    raise ValueError(
                        f"Formato '{formato}' no soportado. "
                        f"Formatos disponibles: {available_formats}"
                    )
            else:
                resultado_parts.append("\n".join(ruts_validos_formateados))

        # Process invalid RUTs
        if ruts_invalidos:
            if resultado_parts:
                resultado_parts.append("")  # Empty line separator
            resultado_parts.append("RUTs inválidos:")
            for rut, error in ruts_invalidos:
                resultado_parts.append(f"{rut} - {error}")

        # Add statistics
        if ruts_validos or ruts_invalidos:
            resultado_parts.extend(
                [
                    "",
                    "Estadísticas de procesamiento:",
                    f"- Total procesados: {resultado_validacion.total_procesados}",
                    f"- RUTs válidos: {len(ruts_validos)}",
                    f"- RUTs inválidos: {len(ruts_invalidos)}",
                    f"- Tasa de éxito: {resultado_validacion.tasa_exito:.1f}%",
                    f"- Tiempo de procesamiento: {resultado_validacion.tiempo_procesamiento:.4f}s",
                ]
            )

        return "\n".join(resultado_parts)


# ============================================================================
# BACKWARDS COMPATIBILITY AND CONVENIENCE FUNCTIONS
# ============================================================================

# Global batch processor instance for backward compatibility
_default_processor = ProcesadorLotesRut()


def formatear_lista_ruts(
    ruts: List[str],
    separador_miles: bool = False,
    mayusculas: bool = False,
    formato: Optional[str] = None,
) -> str:
    """
    Backward compatibility function for the original API.

    This function maintains compatibility with the existing API while
    providing access to the enhanced functionality through the new
    batch processor architecture.

    Args:
        ruts: List of RUT strings to format.
        separador_miles: Whether to add thousand separators.
        mayusculas: Whether to uppercase RUTs.
        formato: Output format (csv, json, xml, None).

    Returns:
        Formatted string with RUTs and validation results.

    Raises:
        ValueError: If parameters are invalid.
    """
    # Issue deprecation warning for future migration
    warnings.warn(
        "formatear_lista_ruts function is deprecated. "
        "Use ProcesadorLotesRut.formatear_lista_ruts para mayor funcionalidad.",
        DeprecationWarning,
        stacklevel=2,
    )

    return _default_processor.formatear_lista_ruts(
        ruts=ruts,
        separador_miles=separador_miles,
        mayusculas=mayusculas,
        formato=formato,
        parallel=False,  # Use sequential processing for backward compatibility
    )


def validar_lista_ruts(ruts: List[str]) -> Dict[str, List[Union[str, Tuple[str, str]]]]:
    """
    Backward compatibility function for RUT list validation.

    Args:
        ruts: List of RUT strings to validate.

    Returns:
        Dictionary with 'validos' and 'invalidos' keys.

    Raises:
        ValueError: If ruts is not a list.
    """
    warnings.warn(
        "validar_lista_ruts function is deprecated. "
        "Use ProcesadorLotesRut.validar_lista_ruts para mayor funcionalidad.",
        DeprecationWarning,
        stacklevel=2,
    )

    result = _default_processor.validar_lista_ruts(ruts, parallel=False)
    return {"validos": result.ruts_validos, "invalidos": result.ruts_invalidos}


# ============================================================================
# MODULE CONFIGURATION AND SETUP
# ============================================================================


def configurar_registro(
    level: int = logging.WARNING, format_string: Optional[str] = None
) -> None:
    """
    Configura el registro del módulo con opciones avanzadas.

    Args:
        level: Nivel de log (por ejemplo, logging.DEBUG, logging.INFO).
        format_string: Cadena de formato personalizada para los mensajes.
    """
    format_string = (
        format_string or "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logging.basicConfig(level=level, format=format_string, force=True)
    logger.setLevel(level)
    logger.info("Registro configurado al nivel: %s", logging.getLevelName(level))


def obtener_informacion_version() -> Dict[str, str]:
    """
    Obtiene la información de versión y metadatos del módulo.

    Returns:
        Diccionario con los metadatos de la versión.
    """
    from . import __version__

    return {
        "version": __version__,
        "author": "Carlos Ortega González",
        "license": "MIT",
        "description": "Enhanced Chilean RUT validation and formatting library",
        "features": [
            "High-performance validation with caching",
            "Parallel batch processing",
            "Comprehensive error handling",
            "Multiple output formats",
            "Configurable validation modes",
            "Performance monitoring",
            "Thread-safe operations",
        ],
    }


def evaluar_rendimiento(num_ruts: int = 10000, parallel: bool = True) -> Dict[str, Any]:
    """
    Evalúa el rendimiento del procesamiento de RUTs.

    Args:
        num_ruts: Cantidad de RUTs de prueba a generar.
        parallel: Si se debe probar el procesamiento en paralelo.

    Returns:
        Diccionario con los resultados del benchmark.
    """

    # Generate test RUTs
    test_ruts = []
    for _ in range(num_ruts):
        base = str(random.randint(1000000, 99999999))
        digit = calcular_digito_verificador(base)
        test_ruts.append(f"{base}-{digit}")

    processor = ProcesadorLotesRut()

    # Benchmark validation
    start_time = time.perf_counter()
    result = processor.validar_lista_ruts(test_ruts, parallel=parallel)
    validation_time = time.perf_counter() - start_time

    # Benchmark formatting
    start_time = time.perf_counter()
    processor.formatear_lista_ruts(
        test_ruts[:1000],  # Limit for formatting benchmark
        separador_miles=True,
        parallel=parallel,
    )
    formatting_time = time.perf_counter() - start_time

    return {
        "test_ruts_count": num_ruts,
        "parallel_processing": parallel,
        "validation_time": validation_time,
        "validation_rate": num_ruts / validation_time,
        "formatting_time": formatting_time,
        "formatting_rate": 1000 / formatting_time,
        "tasa_exito": result.tasa_exito,
        "estadisticas_cache": Rut.estadisticas_cache(),
    }


# ============================================================================
# MODULE INITIALIZATION
# ============================================================================

# Log module initialization
logger.info("Enhanced Rutificador module initialized successfully")

# Export summary for documentation
__all__ = [
    # Core classes
    "Rut",
    "RutBase",
    "ValidadorRut",
    "RutValidator",
    # Exceptions
    "ErrorRut",
    "ErrorValidacionRut",
    "ErrorFormatoRut",
    "ErrorDigitoRut",
    "ErrorLongitudRut",
    "ErrorProcesamientoRut",
    "RutError",
    "RutValidationError",
    "RutFormatError",
    "RutDigitError",
    "RutLengthError",
    "RutProcessingError",
    "RutInvalidoError",
    # Batch processing
    "ProcesadorLotesRut",
    "ResultadoLote",
    # Formatting
    "FormateadorRut",
    "FormateadorCSV",
    "FormateadorXML",
    "FormateadorJSON",
    "FabricaFormateadorRut",
    # Utility functions
    "calcular_digito_verificador",
    "normalizar_base_rut",
    "formatear_lista_ruts",
    "validar_lista_ruts",  # Backward compatibility
    # Configuration
    "ConfiguracionRut",
    "RigorValidacion",
    "CONFIGURACION_POR_DEFECTO",
    "configurar_registro",
    "obtener_informacion_version",
    "evaluar_rendimiento",
]
