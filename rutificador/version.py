import re
from pathlib import Path
from typing import List, TypedDict

try:
    from importlib import metadata as importlib_metadata
except ImportError:
    # Fallback para entornos donde importlib.metadata no esté disponible
    import importlib_metadata  # type: ignore # pylint: disable=import-error


def _obtener_version_dinamica() -> str:
    """Intenta obtener la versión de metadatos o del pyproject.toml."""
    # 1. Intentar desde metadatos del sistema (paquete instalado)
    try:
        return importlib_metadata.version("rutificador")
    except (importlib_metadata.PackageNotFoundError, AttributeError):
        pass

    # 2. Intentar desde pyproject.toml (entorno de desarrollo local)
    try:
        ruta_pyproject = Path(__file__).parent.parent / "pyproject.toml"
        if ruta_pyproject.exists():
            with open(ruta_pyproject, "r", encoding="utf-8") as f:
                # Buscamos la versión específicamente bajo la sección [tool.poetry]
                # para evitar confusión con versiones de dependencias.
                content = f.read()
                match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
                if match:
                    return match.group(1)
    except Exception:  # pylint: disable=broad-exception-caught
        pass

    return "0.0.0-dev"


__version__ = _obtener_version_dinamica()


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
