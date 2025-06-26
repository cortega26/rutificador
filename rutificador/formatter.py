import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Sequence, Type

logger = logging.getLogger(__name__)


class RutFormatter(ABC):
    """Abstract base class for RUT formatters with validation."""

    @abstractmethod
    def format(self, ruts: Sequence[str]) -> str:
        """Format a sequence of RUTs."""
        raise NotImplementedError

    def validate_input(self, ruts: Sequence[str]) -> None:
        """Validate input before formatting."""
        if not isinstance(ruts, (list, tuple)):
            raise TypeError(f"Expected sequence, got {type(ruts).__name__}")

        if not ruts:
            logger.warning("Empty RUT sequence provided for formatting")


class CSVFormatter(RutFormatter):
    """Enhanced CSV formatter with configurable options."""

    def __init__(self, header: str = "rut", delimiter: str = "\n") -> None:
        self.header = header
        self.delimiter = delimiter

    def format(self, ruts: Sequence[str]) -> str:
        self.validate_input(ruts)

        if not ruts:
            return f"{self.header}{self.delimiter}"

        escaped_ruts = [str(rut).replace(',', '\\,') for rut in ruts]
        cadena_ruts = self.delimiter.join(escaped_ruts)

        return f"{self.header}{self.delimiter}{cadena_ruts}"


class XMLFormatter(RutFormatter):
    """Enhanced XML formatter with proper escaping and validation."""

    def __init__(self, root_element: str = "root", item_element: str = "rut") -> None:
        self.root_element = root_element
        self.item_element = item_element

    def format(self, ruts: Sequence[str]) -> str:
        self.validate_input(ruts)

        xml_lines = [f"<{self.root_element}>"]

        for rut in ruts:
            rut_escaped = (
                str(rut)
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&#x27;")
            )
            xml_lines.append(f"    <{self.item_element}>{rut_escaped}</{self.item_element}>")

        xml_lines.append(f"</{self.root_element}>")
        return "\n".join(xml_lines)


class JSONFormatter(RutFormatter):
    """Enhanced JSON formatter with configurable structure."""

    def __init__(self, key_name: str = "rut", pretty_print: bool = True) -> None:
        self.key_name = key_name
        self.pretty_print = pretty_print

    def format(self, ruts: Sequence[str]) -> str:
        self.validate_input(ruts)

        ruts_json = [{self.key_name: str(rut)} for rut in ruts]

        return json.dumps(
            ruts_json,
            indent=2 if self.pretty_print else None,
            ensure_ascii=False,
            separators=(",", ": ") if self.pretty_print else (",", ":"),
        )


class RutFormatterFactory:
    """Factory for creating RUT formatters with configuration support."""

    _formatters: Dict[str, Type[RutFormatter]] = {
        "csv": CSVFormatter,
        "xml": XMLFormatter,
        "json": JSONFormatter,
    }

    @classmethod
    def register_formatter(cls, name: str, formatter_class: Type[RutFormatter]) -> None:
        if not issubclass(formatter_class, RutFormatter):
            raise TypeError("Formatter must inherit from RutFormatter")
        cls._formatters[name.lower()] = formatter_class
        logger.info(f"Registered custom formatter: {name}")

    @classmethod
    def get_formatter(cls, formato: str, **kwargs: Any) -> Optional[RutFormatter]:
        if not isinstance(formato, str):
            return None

        formatter_class = cls._formatters.get(formato.lower())
        if formatter_class:
            return formatter_class(**kwargs)
        return None

    @classmethod
    def get_available_formats(cls) -> List[str]:
        return list(cls._formatters.keys())
