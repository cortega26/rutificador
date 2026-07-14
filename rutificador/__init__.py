"""Rutificador: utilidades para validar y formatear RUTs chilenos."""

from typing import List

from .version import __version__, obtener_informacion_version
from .config import ConfiguracionRut, RigorValidacion
from .validador import ValidadorRut
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
)
from .calidad_datos import (
    InformeDuplicados,
    AuditoriaFormato,
    PerfilRut,
    detectar_duplicados,
    auditar_consistencia_formato,
    perfilar_ruts,
)


def _registrar_contribs() -> None:
    """Registra extensiones externas si están disponibles."""
    try:
        from .contrib import (  # pylint: disable=import-outside-toplevel,unused-import
            pandas,  # noqa: F401
        )
    except ImportError:
        pass
    try:
        from .contrib import (  # pylint: disable=import-outside-toplevel,unused-import
            polars,  # noqa: F401
        )
    except ImportError:
        pass


_registrar_contribs()

__author__ = "Carlos Ortega González"
__license__ = "MIT"

__all__: List[str] = [
    "Rut",
    "RutBase",
    "ValidacionResultado",
    "obtener_rut",
    "ValidadorRut",
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
    "ConfiguracionRut",
    "RigorValidacion",
    "InformeDuplicados",
    "AuditoriaFormato",
    "PerfilRut",
    "detectar_duplicados",
    "auditar_consistencia_formato",
    "perfilar_ruts",
    "__version__",
]
