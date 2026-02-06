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


_pydantic = importlib.import_module("pydantic")
BaseModel = getattr(_pydantic, "BaseModel")
ValidationError = getattr(_pydantic, "ValidationError")


class _Modelo(BaseModel):  # pylint: disable=too-few-public-methods
    rut: RutStr


def _primer_error(exc: ValidationError) -> dict:
    errores = exc.errors()
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
    repo_root = Path(__file__).resolve().parents[3]
    codigo = textwrap.dedent(
        f"""
        import sys
        sys.path.insert(0, {str(repo_root)!r})
        from rutificador.contrib.pydantic._compat import _require_pydantic, PYDANTIC_IMPORT_ERROR_MESSAGE
        try:
            _require_pydantic()
        except ImportError as exc:
            print(str(exc))
            raise SystemExit(0)
        raise SystemExit(1)
        """
    ).strip()

    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env["PYTHONNOUSERSITE"] = "1"

    proceso = subprocess.run(
        [sys.executable, "-S", "-c", codigo],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert (
        proceso.returncode == 0
    ), f"stdout:\n{proceso.stdout}\nstderr:\n{proceso.stderr}"
    assert (
        proceso.stdout.strip() == PYDANTIC_IMPORT_ERROR_MESSAGE
    ), f"stdout:\n{proceso.stdout}\nstderr:\n{proceso.stderr}"
