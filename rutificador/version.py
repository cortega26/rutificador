"""Módulo que define la versión de Rutificador."""

from typing import List, TypedDict

__version__ = "1.4.2"


class InformacionVersion(TypedDict):
    """Estructura tipada para la metadata de versión."""

    version: str
    autor: str
    licencia: str
    descripcion: str
    funcionalidades: List[str]


def obtener_informacion_version() -> InformacionVersion:
    """Retorna metadatos de la versión actual."""
    return {
        "version": __version__,
        "autor": "Carlos Ortega González",
        "licencia": "MIT",
        "descripcion": "Librería mejorada para validar y formatear RUT chileno",
        "funcionalidades": [
            "Validación de alto rendimiento con caché",
            "Procesamiento por lotes en paralelo",
            "Modelo de errores estructurado",
            "Múltiples formatos de salida (JSON, CSV, XML)",
            "Motor de sugerencias inteligente (Fuzzy Matching)",
            "Modos de validación configurables",
            "Monitoreo de rendimiento",
            "Operaciones seguras en hilos",
        ],
    }


__all__ = ["__version__", "obtener_informacion_version", "InformacionVersion"]
