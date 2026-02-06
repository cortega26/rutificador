# SECURITY-CRITICAL
from __future__ import annotations

import importlib
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest
from hypothesis import given, strategies as st

from rutificador.contrib.pydantic import RutStr
from rutificador.contrib.pydantic._compat import PYDANTIC_IMPORT_ERROR_MESSAGE
from rutificador.utils import calcular_digito_verificador


modulo_pydantic = importlib.import_module("pydantic")
BaseModel = getattr(modulo_pydantic, "BaseModel")
ValidationError = getattr(modulo_pydantic, "ValidationError")


class _Modelo(BaseModel):  # pylint: disable=too-few-public-methods
    rut: RutStr


def _primer_error(excepcion: ValidationError) -> dict:
    errores = excepcion.errors()
    assert errores, "Se esperaba al menos un error"
    return errores[0]


@pytest.mark.parametrize(
    "entrada, esperado",
    [
        ("12.345.678-5", "12345678-5"),
        ("12345678-5", "12345678-5"),
        ("12345678", "12345678-5"),
        ("12.345.670-K", "12345670-k"),
    ],
)
def test_rutstr_normaliza_valores_validos(entrada: str, esperado: str) -> None:
    m = _Modelo(rut=entrada)
    assert isinstance(m.rut, RutStr)
    assert m.rut == esperado


@pytest.mark.parametrize(
    "entrada, tipo, msg, hint",
    [
        (
            "12345678-9",
            "DV_MISMATCH",
            "El dígito verificador no coincide",
            "Corrija el DV según el cálculo",
        ),
        (
            "12..345",
            "FORMAT_DOTS",
            "Separadores de miles inválidos",
            "Use grupos de 3 dígitos",
        ),
        (
            "abc",
            "INVALID_CHARS",
            "El RUT contiene caracteres no permitidos",
            "Use solo dígitos, puntos y guion",
        ),
        (
            "k",
            "RUT_INVALID",
            "RUT inválido",
            "Verifica formato base-dv",
        ),
    ],
)
def test_rutstr_mapea_errores_deterministas(
    entrada: str, tipo: str, msg: str, hint: str
) -> None:
    with pytest.raises(ValidationError) as excinfo:
        _Modelo(rut=entrada)
    err = _primer_error(excinfo.value)
    assert err["type"] == tipo
    assert err["msg"] == msg
    assert err.get("ctx", {}).get("hint") == hint


def test_rutstr_rechaza_tipos_no_str() -> None:
    with pytest.raises(ValidationError) as excinfo:
        _Modelo(rut=123)  # type: ignore[arg-type]
    err = _primer_error(excinfo.value)
    assert err["type"] == "TYPE_ERROR"
    assert err["msg"] == "El RUT debe ser una cadena"
    assert err.get("ctx", {}).get("hint") == "Convierta el valor a str"


def test_rutstr_serializa_json_normalizado() -> None:
    m = _Modelo(rut="12.345.678-5")
    payload = m.model_dump_json()
    assert '"rut":"12345678-5"' in payload.replace(" ", "")


@given(st.integers(min_value=0, max_value=99_999_999).map(str))
def test_rutstr_property_based_dv_ok_pasa_y_dv_bad_falla(base: str) -> None:
    dv_ok = calcular_digito_verificador(base)
    dv_bad = "0" if dv_ok != "0" else "1"
    if dv_bad == dv_ok:
        dv_bad = "k" if dv_ok != "k" else "1"

    m = _Modelo(rut=f"{base}-{dv_ok}")
    assert m.rut == f"{base}-{dv_ok}"

    m2 = _Modelo(rut=base)
    assert m2.rut == f"{base}-{dv_ok}"

    with pytest.raises(ValidationError) as excinfo:
        _Modelo(rut=f"{base}-{dv_bad}")
    err = _primer_error(excinfo.value)
    assert err["type"] == "DV_MISMATCH"


def test_require_pydantic_falla_con_mensaje_determinista_si_no_hay_extra() -> None:
    raiz_repo = Path(__file__).resolve().parents[3]
    # Bandit/Codacy (B603): subprocess sin `shell=True`, argumentos controlados y codigo estatico.
    codigo = textwrap.dedent(
        """
        from rutificador.contrib.pydantic._compat import (
            PYDANTIC_IMPORT_ERROR_MESSAGE,
            _require_pydantic,
        )

        try:
            _require_pydantic()
        except ImportError as exc:
            print(str(exc))
            raise SystemExit(0)

        raise SystemExit(1)
        """
    ).strip()

    entorno = os.environ.copy()
    # No heredar PYTHONPATH del padre: fijamos uno controlado (solo el repo).
    entorno.pop("PYTHONPATH", None)
    entorno["PYTHONPATH"] = str(raiz_repo)
    entorno["PYTHONNOUSERSITE"] = "1"

    proceso = subprocess.run(
        [sys.executable, "-S", "-c", codigo],
        capture_output=True,
        text=True,
        env=entorno,
        check=False,
    )  # nosec B603
    salida_diagnostico = (
        f"salida_estandar:\n{proceso.stdout}\nerror_estandar:\n{proceso.stderr}"
    )
    assert proceso.returncode == 0, salida_diagnostico
    assert proceso.stdout.strip() == PYDANTIC_IMPORT_ERROR_MESSAGE, salida_diagnostico
