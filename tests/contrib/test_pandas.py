"""Pruebas para el accessor de Pandas."""

import pytest

pandas = pytest.importorskip("pandas")

import rutificador.contrib.pandas as _rut_pandas  # noqa: E402, F401 - registro del accessor


def test_es_valido_series():
    s = pandas.Series(["12345678-5", "98765432-1", "1-9"])
    resultado = s.rut.es_valido
    assert list(resultado) == [True, False, True]


def test_validar_series():
    s = pandas.Series(["12345678-5", "invalido"])
    resultado = s.rut.validar()
    assert resultado[0].estado == "valido"
    assert resultado[1].estado == "invalido"


def test_formatear_base_dv():
    s = pandas.Series(["12.345.678-5"])
    resultado = s.rut.formatear(formato="base-dv")
    assert resultado.iloc[0] == "12345678-5"


def test_formatear_miles():
    s = pandas.Series(["12345678-5"])
    resultado = s.rut.formatear(formato="miles")
    assert resultado.iloc[0] == "12.345.678-5"


def test_formatear_canonico():
    s = pandas.Series(["999999-k"])
    resultado = s.rut.formatear(formato="canonico")
    assert resultado.iloc[0] == "999999-K"


def test_formatear_miles_con_guion():
    s = pandas.Series(["999999-k"])
    resultado = s.rut.formatear(formato="miles-con-guion")
    assert resultado.iloc[0] == "999.999-K"


def test_formatear_invalido_retorna_none():
    s = pandas.Series(["invalido"])
    resultado = s.rut.formatear(formato="base-dv")
    assert resultado.iloc[0] is None


def test_normalizar_series():
    s = pandas.Series(["12.345.678-5"])
    resultado = s.rut.normalizar()
    assert resultado.iloc[0] == "12345678-5"
