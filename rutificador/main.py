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
from .config import CONFIGURACION_POR_DEFECTO, RutConfig, RigorValidacion
from .exceptions import (
    RutError,
    RutValidationError,
    RutFormatError,
    RutDigitError,
    RutLengthError,
    RutProcessingError,
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

# Type definitions
FormatoOutput = Literal["csv", "xml", "json"]
ModoValidacion = Literal["strict", "lenient", "legacy"]


# ============================================================================
# ENHANCED VALIDATION LAYER
# ============================================================================


@runtime_checkable
class Validator(Protocol):  # pylint: disable=too-few-public-methods
    """Protocol for RUT validators."""

    def validate(self, rut_string: str) -> bool:
        """Validate a RUT string."""
        pass


class RutValidator:
    """
    Enhanced RUT validator with configurable strictness levels.

    This validator implements multiple validation modes to handle
    different use cases and legacy RUT formats while maintaining
    high performance through compiled regex patterns.
    """

    def __init__(
        self,
        config: RutConfig = CONFIGURACION_POR_DEFECTO,
        mode: RigorValidacion = RigorValidacion.ESTRICTO,
    ) -> None:
        """
        Inicializa el validador con la configuración y el nivel de rigurosidad.

        Args:
            config: Objeto de configuración con los parámetros de validación.
            mode: Nivel de rigurosidad para la validación.
        """
        self.config = config
        self.mode = mode
        logger.debug("RutValidator initialized with mode: %s", mode.value)

    def validar_formato(self, rut_string: str) -> re.Match[str]:
        """
        Validate RUT format with enhanced error reporting.

        Args:
            rut_string: The RUT string to validate.

        Returns:
            Match object containing the parsed RUT components.

        Raises:
            RutFormatError: If the format is invalid.

        Examples:
            >>> validator = RutValidator()
            >>> match = validator.validar_formato("12345678-5")
            >>> match.group(1)  # Base number
            '12345678'
            >>> match.group(3)  # Verification digit
            '5'
        """
        # Type validation with specific error
        if not isinstance(rut_string, str):
            raise RutFormatError(
                str(rut_string), "string with format 'XXXXXXXX-X' or 'XX.XXX.XXX-X'"
            )

        if not rut_string or not rut_string.strip():
            raise RutFormatError("", "non-empty string")

        rut_string = rut_string.strip()

        # Preprocesamiento según el modo de validación
        if self.mode == RigorValidacion.FLEXIBLE:
            rut_string = self._normalizar_entrada(rut_string)

        match = RUT_REGEX.fullmatch(rut_string)
        if not match:
            raise RutFormatError(
                rut_string,
                "XXXXXXXX-X or XX.XXX.XXX-X where X are digits and last X can be 'k'",
            )

        logger.debug("Successfully validated RUT format: %s", rut_string)
        return match

    def validar_base(self, base: str, rut_original: str) -> str:
        """
        Validate and normalize RUT base number with enhanced checks.

        Args:
            base: The RUT base number.
            rut_original: Original RUT string for error context.

        Returns:
            Normalized base number.

        Raises:
            RutFormatError: If base format is invalid.
            RutLengthError: If base length exceeds limits.
        """
        if not isinstance(base, str):
            raise RutFormatError(base, "numeric string")

        if not base or not base.strip():
            raise RutFormatError("", "non-empty numeric string")

        base = base.strip()

        # Validate format using compiled patterns
        if not (BASE_WITH_DOTS_REGEX.match(base) or BASE_DIGITS_ONLY_REGEX.match(base)):
            raise RutFormatError(
                base, "numeric string with optional thousand separators"
            )

        base_normalizada = normalizar_base_rut(base)

        # Length validation
        if len(base_normalizada) > self.config.max_digits:
            raise RutLengthError(
                rut_original, len(base_normalizada), self.config.max_digits
            )

        logger.debug("Base validated and normalized: %s -> %s", base, base_normalizada)
        return base_normalizada

    def validar_digito_verificador(
        self, digito_input: Optional[str], digito_calculado: str
    ) -> None:
        """
        Validate verification digit with case-insensitive comparison.

        Args:
            digito_input: User-provided verification digit.
            digito_calculado: Calculated verification digit.

        Raises:
            RutDigitError: If digits don't match.
        """
        if digito_input is not None:
            if not isinstance(digito_input, str):
                raise RutFormatError(str(digito_input), "single character (0-9 or k/K)")

            # Case-insensitive comparison for 'k' digit
            if digito_input.lower() != digito_calculado.lower():
                raise RutDigitError(digito_input, digito_calculado)

        logger.debug(
            "Verification digit validated: %s == %s", digito_input, digito_calculado
        )

    def _normalizar_entrada(self, rut_string: str) -> str:
        """Normaliza la entrada en modo de validación flexible."""
        # Elimina espacios extra y normaliza los separadores
        normalizado = re.sub(r"\s+", "", rut_string)
        # Maneja variaciones comunes de formato
        normalizado = normalizado.replace("_", "-").replace(
            "–", "-"
        )  # Diferentes tipos de guion
        return normalizado


# ============================================================================
# ENHANCED FORMATTING LAYER
# ============================================================================


# ============================================================================
# ENHANCED DOMAIN MODELS
# ============================================================================


@dataclass(frozen=True)
class RutBase:
    """
    Immutable representation of a RUT base number.

    This class uses dataclass with frozen=True to ensure immutability,
    which provides thread safety and hashability benefits. The validation
    is performed during initialization to ensure data integrity.
    """

    base: str
    rut_original: str

    def __post_init__(self) -> None:
        """Validate base after initialization."""
        if not isinstance(self.rut_original, str):
            raise RutValidationError(
                f"RUT original must be a string, received: {type(self.rut_original).__name__}",
                error_code="TYPE_ERROR",
            )

        # Validate through the enhanced validator
        validator = RutValidator()
        validated_base = validator.validar_base(self.base, self.rut_original)

        # Use object.__setattr__ to set the validated value in frozen dataclass
        object.__setattr__(self, "base", validated_base)

    def __str__(self) -> str:
        return self.base


class Rut:
    """
    Enhanced representation of a complete Chilean RUT.

    This class provides a robust, thread-safe implementation with
    comprehensive validation, performance optimization, and extensive
    error handling capabilities.
    """

    # Class-level cache for commonly used RUTs
    _instance_cache: Dict[str, "Rut"] = {}
    _cache_lock = None  # Will be initialized when needed

    def __init__(
        self,
        rut: Union[str, int],
        validator: Optional[RutValidator] = None,
        enable_caching: bool = True,
    ) -> None:
        """
        Initialize a RUT instance with enhanced validation.

        Args:
            rut: RUT value as string or integer.
            validator: Custom validator instance.
            enable_caching: Whether to use instance caching.

        Raises:
            RutValidationError: If RUT is invalid.

        Examples:
            >>> rut = Rut("12345678-5")
            >>> str(rut)
            '12345678-5'
            >>> rut = Rut(12345678)  # Without verification digit
            >>> str(rut)
            '12345678-5'
        """
        # Initialize thread safety if needed
        if Rut._cache_lock is None:
            Rut._cache_lock = threading.RLock()

        # Enhanced input validation
        if not isinstance(rut, (str, int)):
            raise RutValidationError(
                f"RUT must be a string or integer, received: {type(rut).__name__}",
                error_code="TYPE_ERROR",
            )

        self.rut_string = str(rut).strip()

        if not self.rut_string:
            raise RutValidationError("RUT cannot be empty", error_code="EMPTY_RUT")

        # Check cache first if enabled
        if enable_caching and self.rut_string in Rut._instance_cache:
            cached_instance = Rut._instance_cache[self.rut_string]
            self.__dict__.update(cached_instance.__dict__)
            logger.debug("Retrieved RUT from cache: %s", self.rut_string)
            return

        # Use provided validator or create default
        self.validator = validator or RutValidator()

        # Parse and validate RUT components
        self._analizar_y_validar()

        # Cache the instance if enabled
        if enable_caching and Rut._cache_lock is not None:
            with Rut._cache_lock:
                if len(Rut._instance_cache) < 1000:  # Prevent unlimited growth
                    Rut._instance_cache[self.rut_string] = self
                    logger.debug("Cached RUT instance: %s", self.rut_string)

    def _analizar_y_validar(self) -> None:
        """Analiza y valida los componentes del RUT."""
        # Handle integer input (no verification digit provided)
        if self.rut_string.isdigit():
            self.base_string = self.rut_string
            digito_input = None
            logger.debug("Processing numeric RUT: %s", self.rut_string)
        else:
            # Validate format and extract components
            match_result = self.validator.validar_formato(self.rut_string)
            self.base_string = match_result.group(1)
            digito_input = match_result.group(3)

        # Create base and calculate verification digit
        self.base = RutBase(self.base_string, self.rut_string)
        # ``RutBase`` already returns a normalised base, so avoid
        # normalising it again before computing the verification digit.
        self.digito_verificador = calcular_digito_verificador(self.base.base)

        # Validate verification digit if provided
        self.validator.validar_digito_verificador(digito_input, self.digito_verificador)

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
        custom_separator: str = ".",
    ) -> str:
        """
        Formatea el RUT con diversas opciones de presentación.

        Args:
            separador_miles: Indica si se agregan separadores de miles.
            mayusculas: Indica si el RUT se convierte a mayúsculas.
            custom_separator: Carácter para separar los miles.

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

        if not isinstance(custom_separator, str) or len(custom_separator) != 1:
            raise ValueError("custom_separator must be a single character")

        with self._contexto_formateo():
            rut_str = str(self)

            if separador_miles:
                base_formateada = self._agregar_separador_miles(
                    str(self.base), custom_separator
                )
                rut_str = f"{base_formateada}-{self.digito_verificador}"

            if mayusculas:
                rut_str = rut_str.upper()

            logger.debug("Formatted RUT: %s -> %s", self, rut_str)
            return rut_str

    @staticmethod
    def _agregar_separador_miles(numero: str, separator: str = ".") -> str:
        """
        Agrega separadores de miles con manejo de errores.

        Args:
            numero: Cadena numérica a formatear.
            separator: Carácter separador a utilizar.

        Returns:
            Cadena numérica formateada.

        Raises:
            RutValidationError: Si el número no puede formatearse.
        """
        try:
            # Use string manipulation for better performance on known numeric strings
            if len(numero) <= 3:
                return numero

            # Format from right to left
            reversed_digits = numero[::-1]
            chunks = [
                reversed_digits[i : i + 3] for i in range(0, len(reversed_digits), 3)
            ]
            formatted = separator.join(chunks)
            return formatted[::-1]

        except (ValueError, TypeError) as e:
            raise RutValidationError(
                f"Error formatting number '{numero}': {e}", error_code="FORMAT_ERROR"
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
        validator: Optional[RutValidator] = None,
        max_trabajadores: Optional[int] = None,
        tamano_bloque: int = 1000,
    ) -> None:
        """
        Inicializa el procesador de lotes con la configuración indicada.

        Args:
            validator: Instancia de validador personalizada.
            max_trabajadores: Número máximo de hilos de trabajo.
            tamano_bloque: Tamaño de cada bloque para la ejecución paralela.
        """
        self.validator = validator or RutValidator()
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
                raise RutProcessingError(
                    f"Expected sequence, got {type(ruts).__name__}",
                    error_code="TYPE_ERROR",
                )

            if not ruts:
                logger.warning("Empty RUT sequence provided for validation")
                return ResultadoLote(
                    tiempo_procesamiento=time.perf_counter() - start_time
                )

            # Choose processing strategy based on size and parallel flag
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
            logger.error("Batch validation failed after %.4fs: %s", processing_time, e)
            raise RutProcessingError(
                f"Batch validation failed: {e}", error_code="BATCH_ERROR"
            ) from e

    def _validar_secuencial(self, ruts: Sequence[str]) -> ResultadoLote:
        """Validación secuencial de RUTs."""
        result = ResultadoLote()

        for rut_string in ruts:
            try:
                rut_obj = Rut(str(rut_string), validator=self.validator)
                result.ruts_validos.append(str(rut_obj))
            except (RutError, ValueError, TypeError) as e:
                result.ruts_invalidos.append((str(rut_string), str(e)))

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
                    logger.error("Chunk processing failed: %s", e)
                    # Add all chunk items as invalid
                    for rut_string in chunk:
                        result.ruts_invalidos.append(
                            (str(rut_string), f"Error de procesamiento: {e}")
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
        """
        Format a list of RUTs with enhanced options and parallel processing.

        Args:
            ruts: Sequence of RUT strings to format.
            separador_miles: Whether to add thousand separators.
            mayusculas: Whether to uppercase RUTs.
            formato: Output format (csv, json, xml, None).
            parallel: Whether to use parallel processing.
            **formatter_kwargs: Additional arguments for formatters.

        Returns:
            Formatted string with valid and invalid RUTs.

        Raises:
            ValueError: If parameters are invalid.
            RutProcessingError: If batch processing fails.
        """
        # Enhanced input validation
        if not isinstance(ruts, (list, tuple)):
            raise ValueError(
                f"ruts must be a sequence, received: {type(ruts).__name__}"
            )

        if not isinstance(separador_miles, bool):
            raise ValueError(
                "separador_miles must be bool, received: %s",
                type(separador_miles).__name__,
            )

        if not isinstance(mayusculas, bool):
            raise ValueError(
                "mayusculas must be bool, received: %s",
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
            for rut_string in ruts_validos:
                try:
                    rut_obj = Rut(rut_string, validator=self.validator)
                    formatted_rut = rut_obj.formatear(
                        separador_miles=separador_miles, mayusculas=mayusculas
                    )
                    ruts_validos_formateados.append(formatted_rut)
                except (RutError, ValueError, TypeError) as e:
                    logger.warning(
                        "Formatting failed for valid RUT %s: %s", rut_string, e
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
                        f"Format '{formato}' not supported. "
                        f"Available formats: {available_formats}"
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
    "RutValidator",
    # Exceptions
    "RutError",
    "RutValidationError",
    "RutFormatError",
    "RutDigitError",
    "RutLengthError",
    "RutProcessingError",
    "RutInvalidoError",  # Backward compatibility
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
    "RutConfig",
    "RigorValidacion",
    "CONFIGURACION_POR_DEFECTO",
    "configurar_registro",
    "obtener_informacion_version",
    "evaluar_rendimiento",
]
