# SECURITY-CRITICAL
"""Catálogo de errores y estructuras de detalle para Rutificador."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Literal, Optional, TypedDict


Severidad = Literal["error", "warning"]


class EntradaCatalogo(TypedDict):
    """Entrada tipada del catálogo de errores."""

    mensaje: str
    hint: str
    severidad: Severidad
    recuperable: bool


CATALOGO_ERRORES: Dict[str, EntradaCatalogo] = {
    "TYPE_ERROR": {
        "mensaje": "El RUT debe ser cadena o entero",
        "hint": "Convierta el valor a str o int",
        "severidad": "error",
        "recuperable": False,
    },
    "EMPTY_RUT": {
        "mensaje": "El RUT no puede estar vacío",
        "hint": "Ingrese al menos un dígito",
        "severidad": "error",
        "recuperable": True,
    },
    "INVALID_CHARS": {
        "mensaje": "El RUT contiene caracteres no permitidos",
        "hint": "Use solo dígitos, puntos y guion",
        "severidad": "error",
        "recuperable": False,
    },
    "FORMAT_DOTS": {
        "mensaje": "Separadores de miles inválidos",
        "hint": "Use grupos de 3 dígitos",
        "severidad": "error",
        "recuperable": False,
    },
    "FORMAT_HYPHEN": {
        "mensaje": "Guion inválido en RUT",
        "hint": "Use un solo guion antes del DV",
        "severidad": "error",
        "recuperable": False,
    },
    "LENGTH_MIN": {
        "mensaje": "RUT más corto que el mínimo permitido",
        "hint": "Complete más dígitos",
        "severidad": "error",
        "recuperable": True,
    },
    "LENGTH_MAX": {
        "mensaje": "RUT excede el máximo permitido",
        "hint": "Verifique el número base",
        "severidad": "error",
        "recuperable": False,
    },
    "DV_INVALID": {
        "mensaje": "Dígito verificador inválido",
        "hint": "Use 0-9 o K",
        "severidad": "error",
        "recuperable": False,
    },
    "DV_MISMATCH": {
        "mensaje": "El dígito verificador no coincide",
        "hint": "Corrija el DV según el cálculo",
        "severidad": "error",
        "recuperable": False,
    },
    "NORMALIZED_WS": {
        "mensaje": "Se eliminaron espacios en el RUT",
        "hint": "Ingrese sin espacios",
        "severidad": "warning",
        "recuperable": True,
    },
    "NORMALIZED_DASH": {
        "mensaje": "Se normalizó el separador de DV",
        "hint": "Use guion estándar (-)",
        "severidad": "warning",
        "recuperable": True,
    },
    "NORMALIZED_DOTS": {
        "mensaje": "Se eliminaron separadores de miles",
        "hint": "Ingrese sin puntos para uso interno",
        "severidad": "warning",
        "recuperable": True,
    },
    "NORMALIZED_DV": {
        "mensaje": "Se normalizó el DV a minúscula",
        "hint": "Use 'k' o 'K'",
        "severidad": "warning",
        "recuperable": True,
    },
    "LEADING_ZEROS": {
        "mensaje": "Se eliminaron ceros a la izquierda",
        "hint": "Ingrese la base sin ceros iniciales",
        "severidad": "warning",
        "recuperable": True,
    },
    "MASK_STATE": {
        "mensaje": "Enmascarado no disponible para estado no válido",
        "hint": "Valide el RUT antes de enmascarar",
        "severidad": "error",
        "recuperable": False,
    },
    "TOKEN_KEY_REQUIRED": {
        "mensaje": "Tokenización requiere clave",
        "hint": "Proporcione 'clave'",
        "severidad": "error",
        "recuperable": False,
    },
}


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
) -> DetalleError:
    """Crea un DetalleError a partir del catálogo o con overrides."""

    entrada = CATALOGO_ERRORES.get(codigo)
    mensaje_final = mensaje or (entrada["mensaje"] if entrada else "Error desconocido")
    hint_final = hint or (entrada["hint"] if entrada else "Consulte el catálogo de errores")
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
    "CATALOGO_ERRORES",
    "crear_detalle_error",
]
