# SECURITY-CRITICAL
"""Tipo `RutStr` para Pydantic v2 (extra opt-in).

Contrato:
- Acepta solo `str` (estricto de tipo).
- Valida con `Rut.parse(..., modo=ESTRICTO)` sin modificar el core.
- Normaliza siempre a `base-dv` (DV en minuscula).
- Si el DV falta y la base es valida, calcula el DV.
- Si no hay `DetalleError`, usa un error honesto y determinista:
  type="RUT_INVALID", message="RUT inválido", hint="Verifica formato base-dv".
"""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic_core import PydanticCustomError, core_schema as cs

from rutificador.config import RigorValidacion
from rutificador.rut import Rut
from rutificador.utils import calcular_digito_verificador


class RutStr(str):
    """Tipo `str` validado/normalizado para Pydantic v2 (extra opt-in)."""

    _PATTERN_CANONICO: ClassVar[str] = r"^\d{1,8}-[0-9k]$"
    _EJEMPLOS: ClassVar[list[str]] = ["12.345.678-5", "12345678-5"]

    _ERROR_RUT_INVALID_TYPE: ClassVar[str] = "RUT_INVALID"
    _ERROR_RUT_INVALID_MESSAGE: ClassVar[str] = "RUT inválido"
    _ERROR_RUT_INVALID_HINT: ClassVar[str] = "Verifica formato base-dv"

    _ERROR_TYPE_TYPE: ClassVar[str] = "TYPE_ERROR"
    _ERROR_TYPE_MESSAGE: ClassVar[str] = "El RUT debe ser una cadena"
    _ERROR_TYPE_HINT: ClassVar[str] = "Convierta el valor a str"

    @classmethod
    def _error(cls, *, type_code: str, message: str, hint: str) -> PydanticCustomError:
        return PydanticCustomError(type_code, message, {"hint": hint})

    @classmethod
    def _validar_y_normalizar(cls, value: Any) -> "RutStr":
        if not isinstance(value, str):
            raise cls._error(
                type_code=cls._ERROR_TYPE_TYPE,
                message=cls._ERROR_TYPE_MESSAGE,
                hint=cls._ERROR_TYPE_HINT,
            )

        resultado = Rut.parse(value, modo=RigorValidacion.ESTRICTO)

        if resultado.estado == "valid" and resultado.normalizado is not None:
            return cls(resultado.normalizado)

        if (
            resultado.estado == "possible"
            and resultado.base is not None
            and not resultado.errores
        ):
            dv = calcular_digito_verificador(resultado.base).lower()
            return cls(f"{resultado.base}-{dv}")

        if resultado.errores:
            detalle = resultado.errores[0]
            raise PydanticCustomError(
                detalle.codigo,
                detalle.mensaje,
                {"hint": detalle.hint},
            )

        raise cls._error(
            type_code=cls._ERROR_RUT_INVALID_TYPE,
            message=cls._ERROR_RUT_INVALID_MESSAGE,
            hint=cls._ERROR_RUT_INVALID_HINT,
        )

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, _handler: Any
    ) -> cs.CoreSchema:
        # Validator estricto: se encarga del chequeo de tipo (solo str) y del mapping
        # de errores; no dependemos del schema default de `str` para mantener type codes
        # deterministas.
        return cs.no_info_plain_validator_function(
            cls._validar_y_normalizar,
            json_schema_input_schema=cs.str_schema(),
            serialization=cs.to_string_ser_schema(),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, schema: cs.CoreSchema, handler: Any
    ) -> dict[str, Any]:
        json_schema = handler(schema)
        if isinstance(json_schema, dict):
            json_schema.setdefault("type", "string")
            json_schema.setdefault("examples", cls._EJEMPLOS)
            json_schema.setdefault("pattern", cls._PATTERN_CANONICO)
        return json_schema


__all__ = ["RutStr"]
