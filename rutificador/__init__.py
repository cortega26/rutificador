"""Rutificador: utilidades para validar y formatear RUTs chilenos."""

from typing import List, Type, Union

from .version import __version__, obtener_informacion_version
from .validador import Validador, ValidadorRut, RutValidator
from .rut import Rut, RutBase, obtener_rut
from .procesador import (
    DetalleError,
    ProcesadorLotesRut,
    ResultadoLote,
    formatear_lista_ruts,
    formatear_stream_ruts,
    validar_lista_ruts,
    validar_stream_ruts,
    evaluar_rendimiento,
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

__author__ = "Carlos Ortega González"
__license__ = "MIT"

__all__: List[Union[str, Type]] = [
    "Rut",
    "RutBase",
    "obtener_rut",
    "Validador",
    "ValidadorRut",
    "RutValidator",
    "DetalleError",
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
    "formatear_stream_ruts",
    "validar_lista_ruts",
    "validar_stream_ruts",
    "configurar_registro",
    "evaluar_rendimiento",
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
    "__version__",
]
