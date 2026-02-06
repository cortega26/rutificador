"""Módulo que define la versión de Rutificador."""

from typing import List, TypedDict

__version__ = "1.2.0"


class InformacionVersion(TypedDict):
    """Estructura tipada para la metadata de versión."""

    version: str
    author: str
    license: str
    description: str
    features: List[str]


def obtener_informacion_version() -> InformacionVersion:
    """Retorna metadatos de la versión actual."""
    return {
        "version": __version__,
        "author": "Carlos Ortega González",
        "license": "MIT",
        "description": "Librería mejorada para validar y formatear RUT chileno",
        "features": [
            "Validación de alto rendimiento con caché",
            "Procesamiento por lotes en paralelo",
            "Modelo de errores estructurado",
            "Múltiples formatos de salida",
            "Modos de validación configurables",
            "Monitoreo de rendimiento",
            "Operaciones seguras en hilos",
        ],
    }


__all__ = ["__version__", "obtener_informacion_version", "InformacionVersion"]
