"""Módulo que define la versión de Rutificador."""

from typing import Dict

__version__ = "1.0.4"


def obtener_informacion_version() -> Dict[str, str]:
    """Retorna metadatos de la versión actual."""
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


__all__ = ["__version__", "obtener_informacion_version"]
