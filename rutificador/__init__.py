"""Rutificador: utilidades para validar y formatear RUTs chilenos."""

from typing import List

from .version import __version__, obtener_informacion_version
from .config import ConfiguracionRut, RigorValidacion
from .validador import Validador, ValidadorRut
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

_DEPRECATED_EXPORTS: dict[str, str] = {
    "RutConfig": "ConfiguracionRut",
    "RutValidator": "ValidadorRut",
    "RutInvalidoError": "ErrorValidacionRut",
}


def __getattr__(name: str):
    if name in _DEPRECATED_EXPORTS:
        import warnings

        warnings.warn(
            f"{name} está obsoleto, usa {_DEPRECATED_EXPORTS[name]} en su lugar",
            DeprecationWarning,
            stacklevel=2,
        )
        return globals()[_DEPRECATED_EXPORTS[name]]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


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
