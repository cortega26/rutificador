"""Rutificador: utilidades para validar y formatear RUTs chilenos."""

from typing import List

from .version import __version__, obtener_informacion_version
from .config import ConfiguracionRut, RigorValidacion, RutConfig
from .validador import Validador, ValidadorRut, RutValidator
from .rut import Rut, RutBase, ValidacionResultado, obtener_rut
from .procesador import (
    DetalleError,
    RutProcesado,
    ProcesadorLotesRut,
    ResultadoLote,
    formatear_lista_ruts,
    validar_lista_ruts,
    validar_flujo_ruts,
    formatear_flujo_ruts,
    evaluar_rendimiento,
    flujo,
)
from .formatter import (
    FabricaFormateadorRut,
    FormateadorCSV,
    FormateadorXML,
    FormateadorJSON,
)
from .utils import (
    monitor_de_rendimiento,
    calcular_digito_verificador,
    normalizar_base_rut,
    configurar_registro,
    asegurar_cadena_no_vacia,
    asegurar_booleano,
)
from .exceptions import (
    ErrorRut,
    ErrorValidacionRut,
    ErrorFormatoRut,
    ErrorDigitoRut,
    ErrorLongitudRut,
    ErrorProcesamientoRut,
    RutInvalidoError,
)


def _registrar_contribs() -> None:
    """Registra extensiones externas si están disponibles."""
    try:
        from .contrib import pandas  # noqa: F401
    except (ImportError, AttributeError):
        pass
    try:
        from .contrib import polars  # noqa: F401
    except (ImportError, AttributeError):
        pass


_registrar_contribs()

__author__ = "Carlos Ortega González"
__license__ = "MIT"

__all__: List[str] = [
    "Rut",
    "RutBase",
    "ValidacionResultado",
    "obtener_rut",
    "Validador",
    "ValidadorRut",
    "RutValidator",
    "DetalleError",
    "RutProcesado",
    "ProcesadorLotesRut",
    "ResultadoLote",
    "FabricaFormateadorRut",
    "FormateadorCSV",
    "FormateadorXML",
    "FormateadorJSON",
    "monitor_de_rendimiento",
    "calcular_digito_verificador",
    "normalizar_base_rut",
    "formatear_lista_ruts",
    "formatear_flujo_ruts",
    "validar_lista_ruts",
    "validar_flujo_ruts",
    "configurar_registro",
    "evaluar_rendimiento",
    "flujo",
    "asegurar_cadena_no_vacia",
    "asegurar_booleano",
    "obtener_informacion_version",
    "ErrorRut",
    "ErrorValidacionRut",
    "ErrorFormatoRut",
    "ErrorDigitoRut",
    "ErrorLongitudRut",
    "ErrorProcesamientoRut",
    "RutInvalidoError",
    "ConfiguracionRut",
    "RigorValidacion",
    "RutConfig",
    "__version__",
]
