# SECURITY-CRITICAL
"""Tipo `RutStr` para Pydantic v2 (extra opcional; se instala explícitamente).

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
    """Tipo `str` validado/normalizado para Pydantic v2.

    Este tipo pertenece a un extra opcional que se instala explícitamente.
    """

    _PATTERN_CANONICO: ClassVar[str] = r"^\d{1,8}-[0-9k]$"
    _EJEMPLOS: ClassVar[list[str]] = ["12.345.678-5", "12345678-5"]

    _CODIGO_RUT_INVALIDO: ClassVar[str] = "RUT_INVALID"
    _MENSAJE_RUT_INVALIDO: ClassVar[str] = "RUT inválido"
    _PISTA_RUT_INVALIDO: ClassVar[str] = "Verifica formato base-dv"

    _CODIGO_ERROR_TIPO: ClassVar[str] = "TYPE_ERROR"
    _MENSAJE_ERROR_TIPO: ClassVar[str] = "El RUT debe ser una cadena"
    _PISTA_ERROR_TIPO: ClassVar[str] = "Convierta el valor a str"

    @classmethod
    def _error(
        cls, *, codigo_tipo: str, mensaje: str, pista: str
    ) -> PydanticCustomError:
        return PydanticCustomError(codigo_tipo, mensaje, {"hint": pista})

    @classmethod
    def _validar_y_normalizar(cls, valor: Any) -> "RutStr":
        if not isinstance(valor, str):
            raise cls._error(
                codigo_tipo=cls._CODIGO_ERROR_TIPO,
                mensaje=cls._MENSAJE_ERROR_TIPO,
                pista=cls._PISTA_ERROR_TIPO,
            )

        resultado = Rut.parse(valor, modo=RigorValidacion.ESTRICTO)

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
            codigo_tipo=cls._CODIGO_RUT_INVALIDO,
            mensaje=cls._MENSAJE_RUT_INVALIDO,
            pista=cls._PISTA_RUT_INVALIDO,
        )

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _tipo_origen: Any, _manejador: Any
    ) -> cs.CoreSchema:
        # Validador estricto: se encarga del chequeo de tipo (solo str) y del mapeo
        # de errores; no dependemos del esquema por defecto de `str` para mantener
        # códigos de tipo deterministas.
        return cs.no_info_plain_validator_function(
            cls._validar_y_normalizar,
            json_schema_input_schema=cs.str_schema(),
            serialization=cs.to_string_ser_schema(),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, esquema_core: cs.CoreSchema, manejador: Any
    ) -> dict[str, Any]:
        esquema_json = manejador(esquema_core)
        if isinstance(esquema_json, dict):
            esquema_json.setdefault("type", "string")
            esquema_json.setdefault("examples", cls._EJEMPLOS)
            esquema_json.setdefault("pattern", cls._PATTERN_CANONICO)
        return esquema_json


__all__ = ["RutStr"]
