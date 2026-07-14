"""Tests de caracterizacion: comportamiento actual del constructor vs Rut.parse (plan 002).

Estos tests fijan el comportamiento OBSERVADO en commit 278425b."""


import logging

import pytest

from rutificador.config import RigorValidacion
from rutificador.rut import Rut
from rutificador.validador import ValidadorRut

logging.disable(logging.CRITICAL)


def _ctor_valido(s: str) -> bool:
    try:
        Rut(s)
        return True
    except Exception:
        return False


# Tabla derivada empíricamente del comportamiento actual (commit 278425b).
# Columnas: (entrada, ctor_valido, parse_estado)
CASOS = [
    # RUTs completos y válidos
    ("12345678-5", True, "valido"),
    ("12.345.678-5", True, "valido"),
    # Base sola (sin DV): ctor computa el DV, parse dice "posible"
    ("12345678", True, "posible"),
    ("1", True, "posible"),
    ("0", True, "posible"),
    # DV incorrecto: ambos rechazan
    ("12345678-K", False, "invalido"),
    ("12345678-9", False, "invalido"),
    ("999999999-9", False, "invalido"),
    # Solo espacios: ctor rechaza (cadena queda vacía), parse también
    ("  ", False, "invalido"),
    # Caracteres no numéricos: ambos rechazan
    ("abc", False, "invalido"),
]


@pytest.mark.parametrize("entrada, ctor_ok, estado", CASOS)
def test_comportamiento_actual_ctor_y_parse(
    entrada: str, ctor_ok: bool, estado: str
) -> None:
    assert _ctor_valido(entrada) is ctor_ok
    assert Rut.parse(entrada).estado == estado


def test_contrato_builder_vs_clasificador() -> None:
    """Fija el contrato documentado: Rut() es builder (normaliza), parse() es classifier (clasifica).

    El constructor normaliza la entrada (limpia espacios, guiones alternativos, etc.)
    antes de validar, por lo que acepta formatos más permisivos. parse() clasifica
    la cadena tal como llega bajo el modo indicado:
    - ESTRICTO rechaza espacios internos.
    - FLEXIBLE los acepta con una advertencia NORMALIZACION_ESPACIOS.

    Este test pina el contrato acordado en el plan 003 (Opción A: documentar,
    sin cambio de comportamiento). Si en el futuro se elige la Opción B o C,
    actualizar este test refleja visiblemente el cambio.
    """
    entrada = "12 345678-5"
    # Builder: normaliza el espacio y acepta el RUT
    assert _ctor_valido(entrada) is True
    # Classifier ESTRICTO: clasifica el espacio como inválido
    assert Rut.parse(entrada, modo=RigorValidacion.ESTRICTO).estado == "invalido"
    # Classifier FLEXIBLE: normaliza, advierte y acepta
    resultado_flexible = Rut.parse(entrada, modo=RigorValidacion.FLEXIBLE)
    assert resultado_flexible.estado == "valido"
    assert any(
        w.codigo == "NORMALIZACION_ESPACIOS" for w in resultado_flexible.advertencias
    )

