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

from typing import Any, ClassVar, Literal, Type, cast

from pydantic_core import PydanticCustomError, core_schema as cs

from rutificador.config import RigorValidacion
from rutificador.rut import Rut
from rutificador.utils import calcular_digito_verificador

FormatoRut = Literal["base-dv", "canonico", "miles", "miles-con-guion"]


class RutStr(str):
    """Tipo `str` validado/normalizado para Pydantic v2.

    Este tipo pertenece a un extra opcional que se instala explícitamente.
    """

    _PATTERN_BASE: ClassVar[str] = r"^\d{1,8}-[0-9kK]$"
    _EJEMPLOS: ClassVar[list[str]] = ["12.345.678-5", "12345678-5"]

    _TITULO: ClassVar[str] = "Identificador de RUT Chileno"
    _DESCRIPCION: ClassVar[str] = (
        "Cadena que representa un Rol Único Tributario (RUT) chileno. "
        "Se normaliza automáticamente al formato deseado."
    )

    _CODIGO_RUT_INVALIDO: ClassVar[str] = "RUT_INVALIDO"
    _MENSAJE_RUT_INVALIDO: ClassVar[str] = "RUT inválido"
    _PISTA_RUT_INVALIDO: ClassVar[str] = "Verifica formato base-dv"

    _CODIGO_ERROR_TIPO: ClassVar[str] = "ERROR_TIPO"
    _MENSAJE_ERROR_TIPO: ClassVar[str] = "El RUT debe ser una cadena"
    _PISTA_ERROR_TIPO: ClassVar[str] = "Convierta el valor a str"

    @classmethod
    def _error(
        cls, *, codigo_tipo: str, mensaje: str, pista: str
    ) -> PydanticCustomError:
        return PydanticCustomError(codigo_tipo, mensaje, {"hint": pista})

    @classmethod
    def _validar_y_normalizar(
        cls, valor: Any, formato: FormatoRut = "base-dv"
    ) -> "RutStr":
        if not isinstance(valor, str):
            raise cls._error(
                codigo_tipo=cls._CODIGO_ERROR_TIPO,
                mensaje=cls._MENSAJE_ERROR_TIPO,
                pista=cls._PISTA_ERROR_TIPO,
            )

        resultado = Rut.parse(valor, modo=RigorValidacion.ESTRICTO)

        if resultado.estado == "valido" and resultado.normalizado is not None:
            obj = Rut(resultado.normalizado)
            return cls(cls._formatear(obj, formato))

        if (
            resultado.estado == "posible"
            and resultado.base is not None
            and not resultado.errores
        ):
            # Caso donde falta el DV pero la base es viable
            dv = calcular_digito_verificador(resultado.base).lower()
            obj = Rut(f"{resultado.base}-{dv}")
            return cls(cls._formatear(obj, formato))

        if resultado.errores:
            detalle = resultado.errores[0]
            pista = detalle.hint

            # Intentar obtener una sugerencia
            sugerencia = Rut.mejorar(valor)
            if not sugerencia:
                sug_list = Rut.sugerir(valor)
                if sug_list:
                    sugerencia = sug_list[0]

            if sugerencia:
                pista = f"{pista}. ¿Quisiste decir {sugerencia}?"

            raise PydanticCustomError(
                detalle.codigo,
                detalle.mensaje,
                {"hint": pista},
            )

        raise cls._error(
            codigo_tipo=cls._CODIGO_RUT_INVALIDO,
            mensaje=cls._MENSAJE_RUT_INVALIDO,
            pista=cls._PISTA_RUT_INVALIDO,
        )

    @classmethod
    def _formatear(cls, obj: Rut, formato: FormatoRut) -> str:
        if formato == "base-dv":
            return obj.formatear(separador_miles=False)
        if formato == "miles":
            return obj.formatear(separador_miles=True)
        if formato == "canonico":
            return obj.formatear(separador_miles=False, mayusculas=True)
        if formato == "miles-con-guion":
            return obj.formatear(separador_miles=True, mayusculas=True)
        return obj.formatear(separador_miles=False)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _tipo_origen: Any, _manejador: Any
    ) -> cs.CoreSchema:
        # Por defecto usa 'base-dv'
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
            esquema_json.update(
                {
                    "type": "string",
                    "title": cls._TITULO,
                    "description": cls._DESCRIPCION,
                    "examples": cls._EJEMPLOS,
                    "pattern": cls._PATTERN_BASE,
                }
            )
        return esquema_json


def rut_str_annotated(formato: FormatoRut = "base-dv") -> Type[RutStr]:
    """Genera un tipo RutStr con un formato específico para Pydantic."""

    class RutStrForFormat(RutStr):
        """Tipo RutStr especializado para un formato de salida específico."""

        @classmethod
        def __get_pydantic_core_schema__(
            cls, _tipo_origen: Any, _manejador: Any
        ) -> cs.CoreSchema:
            return cs.no_info_plain_validator_function(
                lambda v: cls._validar_y_normalizar(v, formato=formato),
                json_schema_input_schema=cs.str_schema(),
                serialization=cs.to_string_ser_schema(),
            )

    return cast(Type[RutStr], RutStrForFormat)


# Alias para compatibilidad retroactiva
RutStrAnnotated = rut_str_annotated  # pylint: disable=invalid-name


__all__ = ["RutStr", "rut_str_annotated", "RutStrAnnotated", "FormatoRut"]
