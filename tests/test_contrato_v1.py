# pylint: disable=missing-module-docstring

import pytest

from rutificador import ErrorValidacionRut, Rut, flujo
from rutificador.config import RigorValidacion


def _contiene_codigo(detalles, codigo):
    return any(detalle.codigo == codigo for detalle in detalles)


def test_parse_validacion_simple():
    res = Rut.parse("12.345.678-5")
    assert res.estado == "valido"
    assert res.normalizado == "12345678-5"
    assert not res.errores


def test_incremental_typing():
    secuencia = ["", "1", "12", "12.345", "12.345.678-", "12.345.678-5"]
    estados = [Rut.parse(x).estado for x in secuencia]
    assert estados == [
        "incompleto",
        "posible",
        "posible",
        "posible",
        "posible",
        "valido",
    ]


def test_lote_flujo_mixto():
    ruts = ["12.345.678-5", "12.345.678-1", "abc", "9"]
    resultados = list(flujo(ruts))
    assert [r.estado for r in resultados] == [
        "valido",
        "invalido",
        "invalido",
        "posible",
    ]
    assert resultados[1].errores[0].codigo == "DV_DISCORDANTE"


def test_enmascarado():
    assert Rut.enmascarar("12.345.678-5", mantener=3, caracter="X") == "XXXXX678-5"
    assert Rut.enmascarar("12345678-5", mantener=8, caracter="*") == "12345678-5"


def test_tokenizacion():
    tok1 = Rut.enmascarar("12.345.678-5", modo="token", clave="k-secreta")
    tok2 = Rut.enmascarar("12.345.678-5", modo="token", clave="k-secreta")
    assert tok1 == tok2
    assert tok1.startswith("tok_")


def test_error_formato_estable():
    res = Rut.parse("12..345")
    err = res.errores[0]
    assert err.codigo == "FORMATO_PUNTOS"
    assert err.severidad == "error"
    assert err.hint != ""


def test_unicode_guion_normaliza_con_advertencia():
    res = Rut.parse("12.345.678–5")
    assert res.estado == "valido"
    assert _contiene_codigo(res.advertencias, "NORMALIZACION_GUION")


@pytest.mark.parametrize("valor", ["１２３４５６７８-５", "１２３４５６７８–５"])
def test_unicode_fullwidth_digits_aceptado(valor):
    res = Rut.parse(valor)
    assert res.estado == "valido"


def test_formato_guion_multiple():
    res = Rut.parse("12-345-678-5")
    assert res.estado == "invalido"
    assert _contiene_codigo(res.errores, "FORMATO_GUION")


def test_formato_guion_base_vacia():
    res = Rut.parse("-5")
    assert res.estado == "invalido"
    assert _contiene_codigo(res.errores, "FORMATO_GUION")


def test_dv_invalido():
    # DV con múltiples caracteres (pasa filtro de caracteres pero DV inválido)
    res = Rut.parse("12-34")
    assert res.estado == "invalido"
    assert _contiene_codigo(res.errores, "DV_INVALIDO")


def test_longitud_maxima():
    res = Rut.parse("1234567890-5")
    assert res.estado == "invalido"
    assert _contiene_codigo(res.errores, "LONGITUD_MAXIMA")


def test_normalizacion_dv_advertencia():
    res = Rut.parse("999999-K")
    assert res.estado == "valido"
    assert _contiene_codigo(res.advertencias, "NORMALIZACION_DV")


def test_ceros_izquierda_advertencia():
    res = Rut.parse("0012345678-5")
    assert res.estado == "valido"
    assert _contiene_codigo(res.advertencias, "CEROS_IZQUIERDA")


def test_normalizacion_puntos_advertencia():
    res = Rut.parse("12.345.678-5")
    assert res.estado == "valido"
    assert _contiene_codigo(res.advertencias, "NORMALIZACION_PUNTOS")


def test_enmascarado_estado_invalido():
    with pytest.raises(ErrorValidacionRut) as exc:
        Rut.enmascarar("invalido")
    assert exc.value.codigo_error == "ESTADO_ENMASCARADO"


def test_token_clave_requerida():
    with pytest.raises(ErrorValidacionRut) as exc:
        Rut.enmascarar("12.345.678-5", modo="token")
    assert exc.value.codigo_error == "CLAVE_TOKEN_REQUERIDA"


def test_enmascarar_con_separador_miles():
    assert (
        Rut.enmascarar("12.345.678-5", mantener=3, caracter="X", separador_miles=True)
        == "XX.XXX.678-5"
    )


def test_enmascarar_con_mayusculas():
    assert Rut.enmascarar("999999-k", mantener=3, mayusculas=True) == "***999-K"


def test_enmascarar_mantener_cero():
    assert Rut.enmascarar("12.345.678-5", mantener=0, caracter="#") == "########-5"


def test_enmascarar_mantener_excede_base():
    # Cuando mantener > len(base), la base completa es visible
    resultado = Rut.enmascarar("1-9", mantener=5, caracter="X")
    assert resultado == "1-9"


def test_enmascarar_parametro_mantener_invalido():
    with pytest.raises(ErrorValidacionRut):
        Rut.enmascarar("12.345.678-5", mantener="3")


def test_enmascarar_parametro_caracter_invalido():
    with pytest.raises(ErrorValidacionRut):
        Rut.enmascarar("12.345.678-5", caracter="**")


def test_token_con_clave_bytes():
    tok = Rut.enmascarar("12.345.678-5", modo="token", clave=b"k-secreta")
    assert tok.startswith("tok_")


def test_espacios_internos_por_modo():
    normalizado, errores, advertencias = Rut.normalizar(
        "12 345 678-5", modo=RigorValidacion.ESTRICTO
    )
    assert normalizado is None
    assert _contiene_codigo(errores, "CARACTERES_INVALIDOS")

    normalizado, errores, advertencias = Rut.normalizar(
        "12 345 678-5", modo=RigorValidacion.FLEXIBLE
    )
    assert normalizado == "12345678-5"
    assert not errores
    assert _contiene_codigo(advertencias, "NORMALIZACION_ESPACIOS")
