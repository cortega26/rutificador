# pylint: disable=missing-module-docstring

import pytest

from rutificador import ProcesadorLotesRut, Rut
from rutificador.config import RigorValidacion


def _contiene_codigo(detalles, codigo):
    return any(detalle.codigo == codigo for detalle in detalles)


def test_parse_validacion_simple():
    res = Rut.parse("12.345.678-5")
    assert res.estado == "valid"
    assert res.normalizado == "12345678-5"
    assert res.errores == []


def test_incremental_typing():
    secuencia = ["", "1", "12", "12.345", "12.345.678-", "12.345.678-5"]
    estados = [Rut.parse(x).estado for x in secuencia]
    assert estados == [
        "incomplete",
        "possible",
        "possible",
        "possible",
        "possible",
        "valid",
    ]


def test_lote_stream_mixto():
    ruts = ["12.345.678-5", "12.345.678-1", "abc", "9"]
    resultados = list(ProcesadorLotesRut().stream(ruts))
    assert [r.estado for r in resultados] == ["valid", "invalid", "invalid", "possible"]
    assert resultados[1].errores[0].codigo == "DV_MISMATCH"


def test_masking():
    assert Rut.mask("12.345.678-5", keep=3, char="X") == "XXXXX678-5"
    assert Rut.mask("12345678-5", keep=8, char="*") == "12345678-5"


def test_tokenizacion():
    tok1 = Rut.mask("12.345.678-5", modo="token", clave="k-secreta")
    tok2 = Rut.mask("12.345.678-5", modo="token", clave="k-secreta")
    assert tok1 == tok2
    assert tok1.startswith("tok_")


def test_error_format_stable():
    res = Rut.parse("12..345")
    err = res.errores[0]
    assert err.codigo == "FORMAT_DOTS"
    assert err.severidad == "error"
    assert err.hint != ""


def test_unicode_dash_normaliza_con_advertencia():
    res = Rut.parse("12.345.678–5")
    assert res.estado == "valid"
    assert _contiene_codigo(res.advertencias, "NORMALIZED_DASH")


def test_unicode_fullwidth_digits_rechazado():
    res = Rut.parse("１２３４５６７８-５")
    assert res.estado == "invalid"
    assert _contiene_codigo(res.errores, "INVALID_CHARS")


def test_espacios_internos_por_modo():
    normalizado, errores, advertencias = Rut.normalizar(
        "12 345 678-5", modo=RigorValidacion.ESTRICTO
    )
    assert normalizado is None
    assert _contiene_codigo(errores, "INVALID_CHARS")

    normalizado, errores, advertencias = Rut.normalizar(
        "12 345 678-5", modo=RigorValidacion.FLEXIBLE
    )
    assert normalizado == "12345678-5"
    assert errores == []
    assert _contiene_codigo(advertencias, "NORMALIZED_WS")
