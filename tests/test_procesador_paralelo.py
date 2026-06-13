"""Tests de cobertura para las ramas paralelas de ProcesadorLotesRut (plan 002)."""

from rutificador.procesador import (
    ProcesadorLotesRut,
    validar_lista_ruts,
)
from rutificador.utils import calcular_digito_verificador


def _datos(n: int = 60) -> list[str]:
    out = []
    for i in range(1_000_000, 1_000_000 + n):
        b = str(i)
        out.append(f"{b}-{calcular_digito_verificador(b)}")
    return out


def test_validar_lista_paralelo_igual_que_serial() -> None:
    datos = _datos()
    p = ProcesadorLotesRut()
    serial = p.validar_lista_ruts(datos, paralelo=False)
    paralelo = p.validar_lista_ruts(datos, paralelo=True)
    assert sorted(serial.ruts_validos) == sorted(paralelo.ruts_validos)
    assert len(serial.ruts_invalidos) == len(paralelo.ruts_invalidos)
    assert paralelo.total_procesados == len(datos)


def test_funcion_modulo_validar_lista_paralelo() -> None:
    datos = _datos()
    res = validar_lista_ruts(datos, paralelo=True)
    assert len(res["validos"]) == len(datos)
    assert res["invalidos"] == []


def test_validar_lista_paralelo_mezcla_validos_invalidos() -> None:
    datos = _datos(30) + ["no-es-rut", "12345678-9"]
    p = ProcesadorLotesRut()
    serial = p.validar_lista_ruts(datos, paralelo=False)
    paralelo = p.validar_lista_ruts(datos, paralelo=True)
    assert len(serial.ruts_validos) == len(paralelo.ruts_validos)
    assert len(serial.ruts_invalidos) == len(paralelo.ruts_invalidos)
