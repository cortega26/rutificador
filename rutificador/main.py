"""
Enhanced Rutificador main module following industry best practices.

This module provides a robust, high-performance implementation for Chilean RUT
validation and formatting with comprehensive error handling, logging, and
extensibility features.
"""

import json
import logging
import re
from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache, wraps
from typing import (
    Any, Dict, List, Literal, Optional, Protocol, Sequence, 
    Tuple, Union, runtime_checkable, Iterator, Type
)
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

logger = logging.getLogger(__name__)

def setup_logging(level: int = logging.WARNING) -> None:
    """Configure logging for the rutificador module."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

# ============================================================================
# CONFIGURATION AND CONSTANTS
# ============================================================================

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
DEFAULT_CONFIG = RutConfig()

# Regex patterns - compiled once for performance
RUT_REGEX = re.compile(r"^(\d{1,8}(?:\.\d{3})*)(-([0-9kK]))?$")
BASE_WITH_DOTS_REGEX = re.compile(r"^\d{1,3}(?:\.\d{3})*$")
BASE_DIGITS_ONLY_REGEX = re.compile(r"^\d+$")

# Type definitions
FormatoOutput = Literal["csv", "xml", "json"]
ValidationMode = Literal["strict", "lenient", "legacy"]

class ValidationStrictness(Enum):
    """Enumeration for validation strictness levels."""
    STRICT = "strict"
    LENIENT = "lenient"
    LEGACY = "legacy"

# ============================================================================
# ENHANCED EXCEPTION HIERARCHY
# ============================================================================

class RutError(Exception):
    """Base exception for all RUT-related errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, **kwargs: Any) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = kwargs
        logger.error(f"RUT Error [{error_code}]: {message}", extra=kwargs)

class RutValidationError(RutError):
    """Base class for validation-related errors."""
    pass

class RutFormatError(RutValidationError):
    """Raised when RUT format is invalid."""
    
    def __init__(self, rut_value: str, expected_format: str) -> None:
        super().__init__(
            f"Invalid RUT format: '{rut_value}'. Expected format: {expected_format}",
            error_code="FORMAT_ERROR",
            rut_value=rut_value,
            expected_format=expected_format
        )

class RutDigitError(RutValidationError):
    """Raised when verification digit is incorrect."""
    
    def __init__(self, provided_digit: str, calculated_digit: str) -> None:
        super().__init__(
            f"Verification digit mismatch: provided '{provided_digit}', "
            f"calculated '{calculated_digit}'",
            error_code="DIGIT_ERROR",
            provided_digit=provided_digit,
            calculated_digit=calculated_digit
        )

class RutLengthError(RutValidationError):
    """Raised when RUT length is invalid."""
    
    def __init__(self, rut_value: str, length: int, max_length: int) -> None:
        super().__init__(
            f"RUT '{rut_value}' exceeds maximum length: {length} > {max_length}",
            error_code="LENGTH_ERROR",
            rut_value=rut_value,
            length=length,
            max_length=max_length
        )

class RutProcessingError(RutError):
    """Raised during batch processing operations."""
    pass

# Backward compatibility alias
RutInvalidoError = RutValidationError

# ============================================================================
# PERFORMANCE MONITORING
# ============================================================================

def performance_monitor(func):
    """Decorator to monitor function performance."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        import time
        start_time = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            execution_time = time.perf_counter() - start_time
            logger.debug(f"{func.__name__} executed in {execution_time:.4f}s")
            return result
        except Exception as e:
            execution_time = time.perf_counter() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.4f}s: {e}")
            raise
    return wrapper

# ============================================================================
# CORE UTILITIES WITH ENHANCED PERFORMANCE
# ============================================================================

@lru_cache(maxsize=1024)
@performance_monitor
def calcular_digito_verificador(base_numerica: str, config: RutConfig = DEFAULT_CONFIG) -> str:
    """
    Calculate the verification digit for a RUT with optimized performance.
    
    This function uses memoization through LRU cache to avoid recalculating
    verification digits for commonly used RUT bases. The cache size of 1024
    provides good performance for typical usage patterns while maintaining
    reasonable memory usage.
    
    Args:
        base_numerica: The numeric base of the RUT without dots or dashes.
        config: Configuration object with validation parameters.
        
    Returns:
        The verification digit as a string ('0'-'9' or 'k').
        
    Raises:
        RutValidationError: If the numeric base is invalid.
        
    Examples:
        >>> calcular_digito_verificador("12345678")
        '5'
        >>> calcular_digito_verificador("999999")
        'k'
    """
    # Input validation with specific error types
    if not isinstance(base_numerica, str):
        raise RutValidationError(
            f"Numeric base must be a string, received: {type(base_numerica).__name__}",
            error_code="TYPE_ERROR"
        )
    
    if not base_numerica or not base_numerica.strip():
        raise RutValidationError(
            "Numeric base cannot be empty",
            error_code="EMPTY_BASE"
        )
    
    base_numerica = base_numerica.strip()
    
    # Validate that base contains only digits
    if not base_numerica.isdigit():
        raise RutValidationError(
            f"Numeric base '{base_numerica}' must contain only digits",
            error_code="INVALID_DIGITS"
        )

    # Optimized calculation using enumerate for better performance
    suma_parcial = sum(
        int(digit) * config.verification_factors[i % len(config.verification_factors)]
        for i, digit in enumerate(reversed(base_numerica))
    )

    digito_verificador = (
        config.modulo - suma_parcial % config.modulo
    ) % config.modulo

    return str(digito_verificador) if digito_verificador < 10 else "k"

def normalizar_base_rut(base: str) -> str:
    """
    Normalize RUT base by removing dots and leading zeros.
    
    This function handles common formatting variations in RUT input,
    ensuring consistent internal representation while preserving
    the numeric value.
    
    Args:
        base: The RUT base to normalize.
        
    Returns:
        The normalized base string.
        
    Raises:
        RutValidationError: If the base is not a valid string.
        
    Examples:
        >>> normalizar_base_rut("12.345.678")
        '12345678'
        >>> normalizar_base_rut("000001")
        '1'
    """
    if not isinstance(base, str):
        raise RutValidationError(
            f"Base must be a string, received: {type(base).__name__}",
            error_code="TYPE_ERROR"
        )
    
    # Remove dots and leading zeros efficiently
    base_normalizada = base.replace(".", "").lstrip("0")
    return base_normalizada if base_normalizada else "0"

# ============================================================================
# ENHANCED VALIDATION LAYER
# ============================================================================

@runtime_checkable
class Validator(Protocol):
    """Protocol for RUT validators."""
    
    def validate(self, rut_string: str) -> bool:
        """Validate a RUT string."""
        ...

class RutValidator:
    """
    Enhanced RUT validator with configurable strictness levels.
    
    This validator implements multiple validation modes to handle
    different use cases and legacy RUT formats while maintaining
    high performance through compiled regex patterns.
    """

    def __init__(self, config: RutConfig = DEFAULT_CONFIG, 
                 mode: ValidationStrictness = ValidationStrictness.STRICT) -> None:
        """
        Initialize validator with configuration and strictness mode.
        
        Args:
            config: Configuration object with validation parameters.
            mode: Validation strictness level.
        """
        self.config = config
        self.mode = mode
        logger.debug(f"RutValidator initialized with mode: {mode.value}")
    
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
                str(rut_string), 
                "string with format 'XXXXXXXX-X' or 'XX.XXX.XXX-X'"
            )
            
        if not rut_string or not rut_string.strip():
            raise RutFormatError("", "non-empty string")
            
        rut_string = rut_string.strip()
        
        # Apply mode-specific preprocessing
        if self.mode == ValidationStrictness.LENIENT:
            rut_string = self._normalize_input(rut_string)
        
        match = RUT_REGEX.fullmatch(rut_string)
        if not match:
            raise RutFormatError(
                rut_string, 
                "XXXXXXXX-X or XX.XXX.XXX-X where X are digits and last X can be 'k'"
            )

        logger.debug(f"Successfully validated RUT format: {rut_string}")
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
            raise RutFormatError(base, "numeric string with optional thousand separators")

        base_normalizada = normalizar_base_rut(base)

        # Length validation
        if len(base_normalizada) > self.config.max_digits:
            raise RutLengthError(rut_original, len(base_normalizada), self.config.max_digits)

        logger.debug(f"Base validated and normalized: {base} -> {base_normalizada}")
        return base_normalizada

    def validar_digito_verificador(
        self, 
        digito_input: Optional[str], 
        digito_calculado: str
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
                raise RutFormatError(
                    str(digito_input), 
                    "single character (0-9 or k/K)"
                )
            
            # Case-insensitive comparison for 'k' digit
            if digito_input.lower() != digito_calculado.lower():
                raise RutDigitError(digito_input, digito_calculado)
                
        logger.debug(f"Verification digit validated: {digito_input} == {digito_calculado}")

    def _normalize_input(self, rut_string: str) -> str:
        """Normalize input for lenient validation mode."""
        # Remove extra whitespace and normalize separators
        normalized = re.sub(r'\s+', '', rut_string)
        # Handle common formatting variations
        normalized = normalized.replace('_', '-').replace('–', '-')  # Different dash types
        return normalized

# ============================================================================
# ENHANCED FORMATTING LAYER
# ============================================================================

class RutFormatter(ABC):
    """Abstract base class for RUT formatters with validation."""
    
    @abstractmethod
    def format(self, ruts: Sequence[str]) -> str:
        """Format a sequence of RUTs."""
        pass
    
    def validate_input(self, ruts: Sequence[str]) -> None:
        """Validate input before formatting."""
        if not isinstance(ruts, (list, tuple)):
            raise TypeError(f"Expected sequence, got {type(ruts).__name__}")
        
        if not ruts:
            logger.warning("Empty RUT sequence provided for formatting")

class CSVFormatter(RutFormatter):
    """Enhanced CSV formatter with configurable options."""
    
    def __init__(self, header: str = "rut", delimiter: str = "\n") -> None:
        """
        Initialize CSV formatter with customizable options.
        
        Args:
            header: Column header name.
            delimiter: Row delimiter.
        """
        self.header = header
        self.delimiter = delimiter
    
    def format(self, ruts: Sequence[str]) -> str:
        """Format RUTs as CSV with validation."""
        self.validate_input(ruts)
        
        if not ruts:
            return f"{self.header}{self.delimiter}"
        
        # Escape any commas in RUT strings for proper CSV format
        escaped_ruts = [str(rut).replace(',', '\\,') for rut in ruts]
        cadena_ruts = self.delimiter.join(escaped_ruts)
        
        return f"{self.header}{self.delimiter}{cadena_ruts}"

class XMLFormatter(RutFormatter):
    """Enhanced XML formatter with proper escaping and validation."""
    
    def __init__(self, root_element: str = "root", item_element: str = "rut") -> None:
        """
        Initialize XML formatter with customizable element names.
        
        Args:
            root_element: Name of the root XML element.
            item_element: Name of individual RUT elements.
        """
        self.root_element = root_element
        self.item_element = item_element
    
    def format(self, ruts: Sequence[str]) -> str:
        """Format RUTs as XML with proper escaping."""
        self.validate_input(ruts)
        
        xml_lines = [f"<{self.root_element}>"]
        
        for rut in ruts:
            # Comprehensive XML escaping
            rut_escaped = (str(rut)
                          .replace("&", "&amp;")
                          .replace("<", "&lt;")
                          .replace(">", "&gt;")
                          .replace('"', "&quot;")
                          .replace("'", "&#x27;"))
            xml_lines.append(f"    <{self.item_element}>{rut_escaped}</{self.item_element}>")
        
        xml_lines.append(f"</{self.root_element}>")
        return "\n".join(xml_lines)

class JSONFormatter(RutFormatter):
    """Enhanced JSON formatter with configurable structure."""
    
    def __init__(self, key_name: str = "rut", pretty_print: bool = True) -> None:
        """
        Initialize JSON formatter with customizable options.
        
        Args:
            key_name: Key name for RUT values in JSON objects.
            pretty_print: Whether to format JSON with indentation.
        """
        self.key_name = key_name
        self.pretty_print = pretty_print
    
    def format(self, ruts: Sequence[str]) -> str:
        """Format RUTs as JSON with validation."""
        self.validate_input(ruts)
        
        ruts_json = [{self.key_name: str(rut)} for rut in ruts]
        
        return json.dumps(
            ruts_json, 
            indent=2 if self.pretty_print else None,
            ensure_ascii=False,
            separators=(',', ': ') if self.pretty_print else (',', ':')
        )

class RutFormatterFactory:
    """
    Enhanced factory for creating RUT formatters with configuration support.
    
    This factory implements the Factory pattern with support for formatter
    configuration and extensibility through registration of custom formatters.
    """
    
    _formatters: Dict[str, Type[RutFormatter]] = {
        "csv": CSVFormatter,
        "xml": XMLFormatter,
        "json": JSONFormatter,
    }
    
    @classmethod
    def register_formatter(cls, name: str, formatter_class: Type[RutFormatter]) -> None:
        """Register a custom formatter."""
        if not issubclass(formatter_class, RutFormatter):
            raise TypeError("Formatter must inherit from RutFormatter")
        cls._formatters[name.lower()] = formatter_class
        logger.info(f"Registered custom formatter: {name}")
    
    @classmethod
    def get_formatter(cls, formato: str, **kwargs: Any) -> Optional[RutFormatter]:
        """Get formatter instance with optional configuration."""
        if not isinstance(formato, str):
            return None
        
        formatter_class = cls._formatters.get(formato.lower())
        if formatter_class:
            return formatter_class(**kwargs)
        return None
    
    @classmethod
    def get_available_formats(cls) -> List[str]:
        """Get list of available formatter names."""
        return list(cls._formatters.keys())

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
                error_code="TYPE_ERROR"
            )
        
        # Validate through the enhanced validator
        validator = RutValidator()
        validated_base = validator.validar_base(self.base, self.rut_original)
        
        # Use object.__setattr__ to set the validated value in frozen dataclass
        object.__setattr__(self, 'base', validated_base)

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
    _instance_cache: Dict[str, 'Rut'] = {}
    _cache_lock = None  # Will be initialized when needed
    
    def __init__(self, rut: Union[str, int], 
                 validator: Optional[RutValidator] = None,
                 enable_caching: bool = True) -> None:
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
            import threading
            Rut._cache_lock = threading.RLock()
        
        # Enhanced input validation
        if not isinstance(rut, (str, int)):
            raise RutValidationError(
                f"RUT must be a string or integer, received: {type(rut).__name__}",
                error_code="TYPE_ERROR"
            )
        
        self.rut_string = str(rut).strip()
        
        if not self.rut_string:
            raise RutValidationError(
                "RUT cannot be empty",
                error_code="EMPTY_RUT"
            )
        
        # Check cache first if enabled
        if enable_caching and self.rut_string in Rut._instance_cache:
            cached_instance = Rut._instance_cache[self.rut_string]
            self.__dict__.update(cached_instance.__dict__)
            logger.debug(f"Retrieved RUT from cache: {self.rut_string}")
            return

        # Use provided validator or create default
        self.validator = validator or RutValidator()
        
        # Parse and validate RUT components
        self._parse_and_validate()
        
        # Cache the instance if enabled
        if enable_caching:
            with Rut._cache_lock:
                if len(Rut._instance_cache) < 1000:  # Prevent unlimited growth
                    Rut._instance_cache[self.rut_string] = self
                    logger.debug(f"Cached RUT instance: {self.rut_string}")

    def _parse_and_validate(self) -> None:
        """Parse and validate RUT components."""
        # Handle integer input (no verification digit provided)
        if self.rut_string.isdigit():
            self.base_string = self.rut_string
            digito_input = None
            logger.debug(f"Processing numeric RUT: {self.rut_string}")
        else:
            # Validate format and extract components
            match_result = self.validator.validar_formato(self.rut_string)
            self.base_string = match_result.group(1)
            digito_input = match_result.group(3)

        # Create base and calculate verification digit
        self.base = RutBase(self.base_string, self.rut_string)
        self.digito_verificador = calcular_digito_verificador(
            normalizar_base_rut(self.base_string)
        )

        # Validate verification digit if provided
        self.validator.validar_digito_verificador(digito_input, self.digito_verificador)
        
        logger.debug(f"RUT successfully validated: {self}")

    def __str__(self) -> str:
        """String representation of the RUT."""
        return f"{self.base}-{self.digito_verificador}"

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"Rut('{self}')"

    def __eq__(self, other: Any) -> bool:
        """Enhanced equality comparison."""
        if not isinstance(other, Rut):
            return NotImplemented
        return str(self) == str(other)

    def __hash__(self) -> int:
        """Hash implementation for use in sets and dictionaries."""
        return hash(str(self))

    def __lt__(self, other: 'Rut') -> bool:
        """Less than comparison for sorting."""
        if not isinstance(other, Rut):
            return NotImplemented
        return int(self.base.base) < int(other.base.base)

    @contextmanager
    def _formatting_context(self) -> Iterator[None]:
        """Context manager for formatting operations."""
        logger.debug(f"Starting format operation for RUT: {self}")
        try:
            yield
        except Exception as e:
            logger.error(f"Formatting failed for RUT {self}: {e}")
            raise
        finally:
            logger.debug(f"Completed format operation for RUT: {self}")

    def formatear(self, separador_miles: bool = False, 
                  mayusculas: bool = False,
                  custom_separator: str = ".") -> str:
        """
        Format RUT with enhanced options and validation.

        Args:
            separador_miles: Whether to add thousand separators.
            mayusculas: Whether to uppercase the RUT.
            custom_separator: Custom thousand separator character.

        Returns:
            Formatted RUT string.
            
        Raises:
            ValueError: If parameters are invalid.
            
        Examples:
            >>> rut = Rut("12345678-5")
            >>> rut.formatear(separador_miles=True)
            '12.345.678-5'
            >>> rut.formatear(mayusculas=True, custom_separator=",")
            '12345678-5'  # No 'k' digit to uppercase
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

        with self._formatting_context():
            rut_str = str(self)

            if separador_miles:
                base_formateada = self._agregar_separador_miles(
                    str(self.base), custom_separator
                )
                rut_str = f"{base_formateada}-{self.digito_verificador}"

            if mayusculas:
                rut_str = rut_str.upper()

            logger.debug(f"Formatted RUT: {self} -> {rut_str}")
            return rut_str

    @staticmethod
    def _agregar_separador_miles(numero: str, separator: str = ".") -> str:
        """
        Add thousand separators with enhanced error handling.
        
        Args:
            numero: Number string to format.
            separator: Separator character to use.
            
        Returns:
            Formatted number string.
            
        Raises:
            RutValidationError: If number cannot be formatted.
        """
        try:
            # Use string manipulation for better performance on known numeric strings
            if len(numero) <= 3:
                return numero
            
            # Format from right to left
            reversed_digits = numero[::-1]
            chunks = [reversed_digits[i:i+3] for i in range(0, len(reversed_digits), 3)]
            formatted = separator.join(chunks)
            return formatted[::-1]
            
        except (ValueError, TypeError) as e:
            raise RutValidationError(
                f"Error formatting number '{numero}': {e}",
                error_code="FORMAT_ERROR"
            ) from e

    @classmethod
    def clear_cache(cls) -> None:
        """Clear the instance cache."""
        with cls._cache_lock:
            cls._instance_cache.clear()
            logger.info("RUT instance cache cleared")

    @classmethod
    def cache_stats(cls) -> Dict[str, int]:
        """Get cache statistics."""
        with cls._cache_lock:
            return {
                "cache_size": len(cls._instance_cache),
                "max_cache_size": 1000
            }

# ============================================================================
# ADVANCED BATCH PROCESSING SERVICE
# ============================================================================

@dataclass
class BatchResult:
    """Result container for batch processing operations."""
    valid_ruts: List[str] = field(default_factory=list)
    invalid_ruts: List[Tuple[str, str]] = field(default_factory=list)
    processing_time: float = 0.0
    total_processed: int = 0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_processed == 0:
            return 0.0
        return (len(self.valid_ruts) / self.total_processed) * 100

class RutBatchProcessor:
    """
    Advanced batch processing service with parallel processing capabilities.
    
    This service provides high-performance batch processing of RUTs with
    support for parallel execution, progress tracking, and comprehensive
    error handling.
    """
    
    def __init__(self, validator: Optional[RutValidator] = None,
                 max_workers: Optional[int] = None,
                 chunk_size: int = 1000) -> None:
        """
        Initialize batch processor with configuration.
        
        Args:
            validator: Custom validator instance.
            max_workers: Maximum number of worker threads.
            chunk_size: Size of processing chunks for parallel execution.
        """
        self.validator = validator or RutValidator()
        self.max_workers = max_workers
        self.chunk_size = chunk_size
        logger.info(f"BatchProcessor initialized with chunk_size={chunk_size}")
    
    @performance_monitor
    def validar_lista_ruts(self, ruts: Sequence[str], 
                          parallel: bool = True) -> BatchResult:
        """
        Validate a list of RUTs with optional parallel processing.
        
        Args:
            ruts: Sequence of RUT strings to validate.
            parallel: Whether to use parallel processing.
            
        Returns:
            BatchResult with validation results and statistics.
            
        Raises:
            RutProcessingError: If batch processing fails.
        """
        import time
        start_time = time.perf_counter()
        
        try:
            if not isinstance(ruts, (list, tuple)):
                raise RutProcessingError(
                    f"Expected sequence, got {type(ruts).__name__}",
                    error_code="TYPE_ERROR"
                )
            
            if not ruts:
                logger.warning("Empty RUT sequence provided for validation")
                return BatchResult(processing_time=time.perf_counter() - start_time)
            
            # Choose processing strategy based on size and parallel flag
            if parallel and len(ruts) > self.chunk_size:
                result = self._validate_parallel(ruts)
            else:
                result = self._validate_sequential(ruts)
            
            result.processing_time = time.perf_counter() - start_time
            result.total_processed = len(ruts)
            
            logger.info(
                f"Batch validation completed: {len(result.valid_ruts)} valid, "
                f"{len(result.invalid_ruts)} invalid, "
                f"success rate: {result.success_rate:.1f}%"
            )
            
            return result
            
        except Exception as e:
            processing_time = time.perf_counter() - start_time
            logger.error(f"Batch validation failed after {processing_time:.4f}s: {e}")
            raise RutProcessingError(
                f"Batch validation failed: {e}",
                error_code="BATCH_ERROR"
            ) from e
    
    def _validate_sequential(self, ruts: Sequence[str]) -> BatchResult:
        """Sequential validation of RUTs."""
        result = BatchResult()
        
        for rut_string in ruts:
            try:
                rut_obj = Rut(str(rut_string), validator=self.validator)
                result.valid_ruts.append(str(rut_obj))
            except (RutError, ValueError, TypeError) as e:
                result.invalid_ruts.append((str(rut_string), str(e)))
        
        return result
    
    def _validate_parallel(self, ruts: Sequence[str]) -> BatchResult:
        """Parallel validation of RUTs using ThreadPoolExecutor."""
        result = BatchResult()
        chunks = [ruts[i:i + self.chunk_size] for i in range(0, len(ruts), self.chunk_size)]
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_chunk = {
                executor.submit(self._validate_chunk, chunk): chunk 
                for chunk in chunks
            }
            
            for future in as_completed(future_to_chunk):
                try:
                    chunk_result = future.result()
                    result.valid_ruts.extend(chunk_result.valid_ruts)
                    result.invalid_ruts.extend(chunk_result.invalid_ruts)
                except Exception as e:
                    chunk = future_to_chunk[future]
                    logger.error(f"Chunk processing failed: {e}")
                    # Add all chunk items as invalid
                    for rut_string in chunk:
                        result.invalid_ruts.append((str(rut_string), f"Processing error: {e}"))
        
        return result
    
    def _validate_chunk(self, chunk: Sequence[str]) -> BatchResult:
        """Validate a chunk of RUTs."""
        return self._validate_sequential(chunk)
    
    @performance_monitor
    def formatear_lista_ruts(
        self,
        ruts: Sequence[str],
        separador_miles: bool = False,
        mayusculas: bool = False,
        formato: Optional[FormatoOutput] = None,
        parallel: bool = True,
        **formatter_kwargs: Any
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
            raise ValueError(f"ruts must be a sequence, received: {type(ruts).__name__}")
        
        if not isinstance(separador_miles, bool):
            raise ValueError(f"separador_miles must be bool, received: {type(separador_miles).__name__}")
            
        if not isinstance(mayusculas, bool):
            raise ValueError(f"mayusculas must be bool, received: {type(mayusculas).__name__}")
        
        # Validate RUTs
        resultado_validacion = self.validar_lista_ruts(ruts, parallel=parallel)
        ruts_validos = resultado_validacion.valid_ruts
        ruts_invalidos = resultado_validacion.invalid_ruts
        
        resultado_parts = []
        
        # Process valid RUTs
        if ruts_validos:
            ruts_validos_formateados = []
            for rut_string in ruts_validos:
                try:
                    rut_obj = Rut(rut_string, validator=self.validator)
                    formatted_rut = rut_obj.formatear(
                        separador_miles=separador_miles, 
                        mayusculas=mayusculas
                    )
                    ruts_validos_formateados.append(formatted_rut)
                except (RutError, ValueError, TypeError) as e:
                    logger.warning(f"Formatting failed for valid RUT {rut_string}: {e}")
                    continue

            resultado_parts.append("Valid RUTs:")
            
            # Apply specific format if requested
            if formato:
                formatter = RutFormatterFactory.get_formatter(formato, **formatter_kwargs)
                if formatter:
                    resultado_parts.append(formatter.format(ruts_validos_formateados))
                else:
                    available_formats = RutFormatterFactory.get_available_formats()
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
            resultado_parts.append("Invalid RUTs:")
            for rut, error in ruts_invalidos:
                resultado_parts.append(f"{rut} - {error}")

        # Add statistics
        if ruts_validos or ruts_invalidos:
            resultado_parts.extend([
                "",
                f"Processing Statistics:",
                f"- Total processed: {resultado_validacion.total_processed}",
                f"- Valid RUTs: {len(ruts_validos)}",
                f"- Invalid RUTs: {len(ruts_invalidos)}",
                f"- Success rate: {resultado_validacion.success_rate:.1f}%",
                f"- Processing time: {resultado_validacion.processing_time:.4f}s"
            ])

        return "\n".join(resultado_parts)


# ============================================================================
# BACKWARDS COMPATIBILITY AND CONVENIENCE FUNCTIONS
# ============================================================================

# Global batch processor instance for backward compatibility
_default_processor = RutBatchProcessor()

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
        "Use RutBatchProcessor.formatear_lista_ruts for enhanced functionality.",
        DeprecationWarning,
        stacklevel=2
    )
    
    return _default_processor.formatear_lista_ruts(
        ruts=ruts,
        separador_miles=separador_miles,
        mayusculas=mayusculas,
        formato=formato,
        parallel=False  # Use sequential processing for backward compatibility
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
        "Use RutBatchProcessor.validar_lista_ruts for enhanced functionality.",
        DeprecationWarning,
        stacklevel=2
    )
    
    result = _default_processor.validar_lista_ruts(ruts, parallel=False)
    return {
        "validos": result.valid_ruts,
        "invalidos": result.invalid_ruts
    }

# ============================================================================
# MODULE CONFIGURATION AND SETUP
# ============================================================================

def configure_logging(level: int = logging.WARNING, 
                     format_string: Optional[str] = None) -> None:
    """
    Configure module-wide logging with enhanced options.
    
    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
        format_string: Custom format string for log messages.
    """
    format_string = format_string or '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=level, format=format_string, force=True)
    logger.setLevel(level)
    logger.info(f"Rutificador logging configured at level: {logging.getLevelName(level)}")

def get_version_info() -> Dict[str, str]:
    """
    Get version and module information.
    
    Returns:
        Dictionary with version and module metadata.
    """
    return {
        "version": "0.4.1",
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
            "Thread-safe operations"
        ]
    }

def benchmark_performance(num_ruts: int = 10000, 
                         parallel: bool = True) -> Dict[str, Any]:
    """
    Benchmark the performance of RUT processing.
    
    Args:
        num_ruts: Number of test RUTs to generate.
        parallel: Whether to test parallel processing.
        
    Returns:
        Dictionary with benchmark results.
    """
    import time
    import random
    
    # Generate test RUTs
    test_ruts = []
    for _ in range(num_ruts):
        base = str(random.randint(1000000, 99999999))
        digit = calcular_digito_verificador(base)
        test_ruts.append(f"{base}-{digit}")
    
    processor = RutBatchProcessor()
    
    # Benchmark validation
    start_time = time.perf_counter()
    result = processor.validar_lista_ruts(test_ruts, parallel=parallel)
    validation_time = time.perf_counter() - start_time
    
    # Benchmark formatting
    start_time = time.perf_counter()
    formatted = processor.formatear_lista_ruts(
        test_ruts[:1000],  # Limit for formatting benchmark
        separador_miles=True,
        parallel=parallel
    )
    formatting_time = time.perf_counter() - start_time
    
    return {
        "test_ruts_count": num_ruts,
        "parallel_processing": parallel,
        "validation_time": validation_time,
        "validation_rate": num_ruts / validation_time,
        "formatting_time": formatting_time,
        "formatting_rate": 1000 / formatting_time,
        "success_rate": result.success_rate,
        "cache_stats": Rut.cache_stats()
    }

# ============================================================================
# MODULE INITIALIZATION
# ============================================================================

# Set up default logging
setup_logging()

# Log module initialization
logger.info("Enhanced Rutificador module initialized successfully")

# Export summary for documentation
__all__ = [
    # Core classes
    'Rut', 'RutBase', 'RutValidator', 
    # Exceptions
    'RutError', 'RutValidationError', 'RutFormatError', 
    'RutDigitError', 'RutLengthError', 'RutProcessingError',
    'RutInvalidoError',  # Backward compatibility
    # Batch processing
    'RutBatchProcessor', 'BatchResult',
    # Formatting
    'RutFormatter', 'CSVFormatter', 'XMLFormatter', 'JSONFormatter',
    'RutFormatterFactory',
    # Utility functions
    'calcular_digito_verificador', 'normalizar_base_rut',
    'formatear_lista_ruts', 'validar_lista_ruts',  # Backward compatibility
    # Configuration
    'RutConfig', 'ValidationStrictness', 'DEFAULT_CONFIG',
    'configure_logging', 'get_version_info', 'benchmark_performance'
]