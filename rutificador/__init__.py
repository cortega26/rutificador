"""
Rutificador: Una biblioteca Python para validar y formatear RUTs chilenos.

Este módulo proporciona herramientas para trabajar con RUTs chilenos (Rol Único Tributario),
incluyendo validación, formateo y verificación de dígitos.

Clases:
    Rut: Representa un RUT chileno, con métodos para validación y formateo.
    RutDigitoVerificador: Calcula y representa el dígito verificador de un RUT chileno.
    RutInvalidoError: Excepción personalizada para errores de RUT inválido.
"""

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    import tomli as tomllib
from typing import List, Type, Union

# Version info
try:
    __version__ = version("rutificador")
except PackageNotFoundError:  # Fallback for local runs without installation
    with open(Path(__file__).resolve().parent.parent / "pyproject.toml", "rb") as f:
        __version__ = tomllib.load(f)["tool"]["poetry"]["version"]
__author__ = "Carlos Ortega González"
__license__ = "MIT"

# Core classes
from rutificador.main import Rut, RutBase, RutInvalidoError, RutValidator

# Processing and formatting
from rutificador.main import RutBatchProcessor
from rutificador.formatter import (
    RutFormatterFactory,
    CSVFormatter,
    XMLFormatter,
    JSONFormatter,
)

# Utility functions
from rutificador.main import (
    calcular_digito_verificador,
    formatear_lista_ruts,
)

# Public API
__all__: List[Union[str, Type]] = [
    # Core classes
    'Rut',
    'RutBase',
    'RutInvalidoError',
    'RutValidator',
    # Processing and formatting
    'RutBatchProcessor',
    'RutFormatterFactory',
    'CSVFormatter',
    'XMLFormatter',
    'JSONFormatter',
    # Utility functions
    'calcular_digito_verificador',
    'formatear_lista_ruts',
]
