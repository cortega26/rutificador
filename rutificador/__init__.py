"""Rutificador: utilidades para validar y formatear RUTs chilenos."""

from .calidad_datos import (
    AuditoriaFormato,
    InformeDuplicados,
    PerfilRut,
    auditar_consistencia_formato,
    detectar_duplicados,
    perfilar_ruts,
)
from .config import ConfiguracionRut, RigorValidacion
from .exceptions import (
    ErrorDigitoRut,
    ErrorFormatoRut,
    ErrorLongitudRut,
    ErrorProcesamientoRut,
    ErrorRut,
    ErrorValidacionRut,
)
from .formatter import (
    FabricaFormateadorRut,
    FormateadorCSV,
    FormateadorJSON,
    FormateadorXML,
)
from .procesador import (
    DetalleError,
    ProcesadorLotesRut,
    ResultadoLote,
    RutProcesado,
    evaluar_rendimiento,
    flujo,
    formatear_flujo_ruts,
    formatear_lista_ruts,
    validar_flujo_ruts,
    validar_lista_ruts,
)
from .rut import Rut, RutBase, ValidacionResultado, obtener_rut
from .utils import (
    asegurar_booleano,
    asegurar_cadena_no_vacia,
    calcular_digito_verificador,
    configurar_registro,
    monitor_de_rendimiento,
    normalizar_base_rut,
)
from .validador import ValidadorRut
from .version import __version__, obtener_informacion_version


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

__all__: list[str] = [
    "AuditoriaFormato",
    "ConfiguracionRut",
    "DetalleError",
    "ErrorDigitoRut",
    "ErrorFormatoRut",
    "ErrorLongitudRut",
    "ErrorProcesamientoRut",
    "ErrorRut",
    "ErrorValidacionRut",
    "FabricaFormateadorRut",
    "FormateadorCSV",
    "FormateadorJSON",
    "FormateadorXML",
    "InformeDuplicados",
    "PerfilRut",
    "ProcesadorLotesRut",
    "ResultadoLote",
    "RigorValidacion",
    "Rut",
    "RutBase",
    "RutProcesado",
    "ValidacionResultado",
    "ValidadorRut",
    "__version__",
    "asegurar_booleano",
    "asegurar_cadena_no_vacia",
    "auditar_consistencia_formato",
    "calcular_digito_verificador",
    "configurar_registro",
    "detectar_duplicados",
    "evaluar_rendimiento",
    "flujo",
    "formatear_flujo_ruts",
    "formatear_lista_ruts",
    "monitor_de_rendimiento",
    "normalizar_base_rut",
    "obtener_informacion_version",
    "obtener_rut",
    "perfilar_ruts",
    "validar_flujo_ruts",
    "validar_lista_ruts",
]
