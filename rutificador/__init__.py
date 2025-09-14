"""
Rutificador: Una biblioteca Python para validar y formatear RUTs chilenos.

Este módulo proporciona herramientas para trabajar con RUTs chilenos
(Rol Único Tributario), incluyendo validación, formateo y verificación
de dígitos.

Clases:
    Rut: Representa un RUT chileno, con métodos para validación y
        formateo.
    RutDigitoVerificador: Calcula y representa el dígito verificador
        de un RUT chileno.
    RutInvalidoError: Excepción personalizada para errores de RUT
        inválido.
"""

from typing import List, Type, Union

from .version import __version__

# Core classes
from rutificador.main import Rut, RutBase, RutInvalidoError, RutValidator

# Processing and formatting
from rutificador.main import ProcesadorLotesRut
from rutificador.formatter import (
    FabricaFormateadorRut,
    FormateadorCSV,
    FormateadorXML,
    FormateadorJSON,
)

# Utility functions
from rutificador.main import (
    calcular_digito_verificador,
    formatear_lista_ruts,
)

__author__ = "Carlos Ortega González"
__license__ = "MIT"

# Public API
__all__: List[Union[str, Type]] = [
    # Core classes
    "Rut",
    "RutBase",
    "RutInvalidoError",
    "RutValidator",
    # Processing and formatting
    "ProcesadorLotesRut",
    "FabricaFormateadorRut",
    "FormateadorCSV",
    "FormateadorXML",
    "FormateadorJSON",
    # Utility functions
    "calcular_digito_verificador",
    "formatear_lista_ruts",
    "__version__",
]
