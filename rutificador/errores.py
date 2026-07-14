# SECURITY-CRITICAL
"""Catálogo de errores y estructuras de detalle para Rutificador."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Literal, Optional, TypedDict

Severidad = Literal["error", "advertencia"]
Idioma = Literal["es", "en"]


class EntradaCatalogo(TypedDict):
    """Entrada tipada del catálogo de errores."""

    mensaje: str
    hint: str
    severidad: Severidad
    recuperable: bool


_CATALOGO_ES: Dict[str, EntradaCatalogo] = {
    "ERROR_TIPO": {
        "mensaje": "El RUT debe ser cadena o entero",
        "hint": "Convierta el valor a str o int",
        "severidad": "error",
        "recuperable": False,
    },
    "RUT_VACIO": {
        "mensaje": "El RUT no puede estar vacío",
        "hint": "Ingrese al menos un dígito",
        "severidad": "error",
        "recuperable": True,
    },
    "CARACTERES_INVALIDOS": {
        "mensaje": "El RUT contiene caracteres no permitidos",
        "hint": "Use solo dígitos, puntos y guion",
        "severidad": "error",
        "recuperable": False,
    },
    "FORMATO_PUNTOS": {
        "mensaje": "Separadores de miles inválidos",
        "hint": "Use grupos de 3 dígitos",
        "severidad": "error",
        "recuperable": False,
    },
    "FORMATO_GUION": {
        "mensaje": "Guion inválido en RUT",
        "hint": "Use un solo guion antes del DV",
        "severidad": "error",
        "recuperable": False,
    },
    "LONGITUD_MINIMA": {
        "mensaje": "RUT más corto que el mínimo permitido",
        "hint": "Complete más dígitos",
        "severidad": "error",
        "recuperable": True,
    },
    "LONGITUD_MAXIMA": {
        "mensaje": "RUT excede el máximo permitido",
        "hint": "Verifique el número base",
        "severidad": "error",
        "recuperable": False,
    },
    "DV_INVALIDO": {
        "mensaje": "Dígito verificador inválido",
        "hint": "Use 0-9 o K",
        "severidad": "error",
        "recuperable": False,
    },
    "DV_DISCORDANTE": {
        "mensaje": "El dígito verificador no coincide",
        "hint": "Corrija el DV según el cálculo",
        "severidad": "error",
        "recuperable": False,
    },
    "NORMALIZACION_ESPACIOS": {
        "mensaje": "Se eliminaron espacios en el RUT",
        "hint": "Ingrese sin espacios",
        "severidad": "advertencia",
        "recuperable": True,
    },
    "NORMALIZACION_GUION": {
        "mensaje": "Se normalizó el separador de DV",
        "hint": "Use guion estándar (-)",
        "severidad": "advertencia",
        "recuperable": True,
    },
    "NORMALIZACION_PUNTOS": {
        "mensaje": "Se eliminaron separadores de miles",
        "hint": "Ingrese sin puntos para uso interno",
        "severidad": "advertencia",
        "recuperable": True,
    },
    "NORMALIZACION_DV": {
        "mensaje": "Se normalizó el DV a minúscula",
        "hint": "Use 'k' o 'K'",
        "severidad": "advertencia",
        "recuperable": True,
    },
    "CEROS_IZQUIERDA": {
        "mensaje": "Se eliminaron ceros a la izquierda",
        "hint": "Ingrese la base sin ceros iniciales",
        "severidad": "advertencia",
        "recuperable": True,
    },
    "ESTADO_ENMASCARADO": {
        "mensaje": "Enmascarado no disponible para estado no válido",
        "hint": "Valide el RUT antes de enmascarar",
        "severidad": "error",
        "recuperable": False,
    },
    "CLAVE_TOKEN_REQUERIDA": {
        "mensaje": "Tokenización requiere clave",
        "hint": "Proporcione 'clave'",
        "severidad": "error",
        "recuperable": False,
    },
}

_CATALOGO_EN: Dict[str, EntradaCatalogo] = {
    "ERROR_TIPO": {
        "mensaje": "RUT must be a string or integer",
        "hint": "Convert the value to str or int",
        "severidad": "error",
        "recuperable": False,
    },
    "RUT_VACIO": {
        "mensaje": "RUT cannot be empty",
        "hint": "Enter at least one digit",
        "severidad": "error",
        "recuperable": True,
    },
    "DV_DISCORDANTE": {
        "mensaje": "Check digit does not match",
        "hint": "Correct the check digit",
        "severidad": "error",
        "recuperable": False,
    },
}

_LOCALE_CATALOGS: Dict[Idioma, Dict[str, EntradaCatalogo]] = {
    "es": _CATALOGO_ES,
    "en": _CATALOGO_EN,
}

CATALOGO_ERRORES = _CATALOGO_ES


@dataclass(frozen=True)
class DetalleError:
    """Detalle estructurado de error o advertencia."""

    codigo: str
    mensaje: str
    hint: str
    severidad: Severidad
    recuperable: bool
    rut: Optional[str] = None
    duracion: float = 0.0

    def __eq__(self, other: object) -> bool:  # pragma: no cover - comparación simple
        if not isinstance(other, DetalleError):
            return NotImplemented
        return (
            self.codigo,
            self.mensaje,
            self.hint,
            self.severidad,
            self.recuperable,
            self.rut,
        ) == (
            other.codigo,
            other.mensaje,
            other.hint,
            other.severidad,
            other.recuperable,
            other.rut,
        )


def crear_detalle_error(
    codigo: str,
    *,
    mensaje: Optional[str] = None,
    hint: Optional[str] = None,
    severidad: Optional[Severidad] = None,
    recuperable: Optional[bool] = None,
    rut: Optional[str] = None,
    duracion: float = 0.0,
    idioma: Idioma = "es",
) -> DetalleError:
    """Crea un DetalleError a partir del catálogo o con overrides.

    Args:
        codigo: Código de error del catálogo.
        mensaje: Override del mensaje.
        hint: Override del hint.
        severidad: Override de la severidad.
        recuperable: Override de recuperabilidad.
        rut: RUT asociado al error.
        duracion: Tiempo de procesamiento.
        idioma: Idioma para los mensajes (``"es"`` o ``"en"``).
            Si la entrada no existe en el idioma solicitado, se usa
            el catálogo en español como fallback.
    """

    catalogo = _LOCALE_CATALOGS.get(idioma, _CATALOGO_ES)
    entrada = catalogo.get(codigo)
    if entrada is None and idioma != "es":
        entrada = _CATALOGO_ES.get(codigo)

    mensaje_final = mensaje or (entrada["mensaje"] if entrada else "Error desconocido")
    hint_final = hint or (
        entrada["hint"] if entrada else "Consulte el catálogo de errores"
    )
    severidad_final = severidad or (entrada["severidad"] if entrada else "error")
    recuperable_final = (
        recuperable
        if recuperable is not None
        else (entrada["recuperable"] if entrada else False)
    )
    return DetalleError(
        codigo=codigo,
        mensaje=mensaje_final,
        hint=hint_final,
        severidad=severidad_final,
        recuperable=recuperable_final,
        rut=rut,
        duracion=duracion,
    )


__all__ = [
    "DetalleError",
    "Severidad",
    "Idioma",
    "CATALOGO_ERRORES",
    "crear_detalle_error",
]
