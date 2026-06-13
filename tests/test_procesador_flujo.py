"""Tests de regresión para el procesamiento paralelo en flujo (plan 001).

Verifican que el modo paralelo de validar_flujo_ruts y formatear_flujo_ruts:
- acepta generadores puros (sin __len__), lo que garantiza que no se llame len()
  sobre el iterable de entrada;
- produce los mismos resultados que el modo serial;
- respeta un chunksize personalizado.
"""

from rutificador.procesador import (
    validar_flujo_ruts,
    formatear_flujo_ruts,
    CHUNKSIZE_FLUJO_POR_DEFECTO,
)
from rutificador.utils import calcular_digito_verificador


def _muestra(n: int = 50):
    """Generador puro (sin __len__) de RUTs válidos consecutivos."""
    for i in range(1_000_000, 1_000_000 + n):
        b = str(i)
        yield f"{b}-{calcular_digito_verificador(b)}"


def test_constante_chunksize_definida():
    assert CHUNKSIZE_FLUJO_POR_DEFECTO > 1


def test_flujo_paralelo_acepta_generador():
    """Un generador sin __len__ no debe provocar TypeError en el modo paralelo."""
    resultados = list(validar_flujo_ruts(_muestra(50), paralelo=True))
    assert len(resultados) == 50
    assert all(es_valido for es_valido, _ in resultados)


def test_flujo_paralelo_igual_que_serial():
    """El modo paralelo debe producir los mismos resultados que el serial."""
    datos = list(_muestra(100))
    serial = [
        (ok, getattr(d, "valor", None))
        for ok, d in validar_flujo_ruts(datos, paralelo=False)
    ]
    paralelo = [
        (ok, getattr(d, "valor", None))
        for ok, d in validar_flujo_ruts(datos, paralelo=True)
    ]
    assert serial == paralelo


def test_flujo_paralelo_chunksize_personalizado():
    """Un chunksize distinto al defecto debe seguir produciendo resultados correctos."""
    datos = list(_muestra(20))
    res = list(validar_flujo_ruts(datos, paralelo=True, chunksize=4))
    assert len(res) == 20
    assert all(ok for ok, _ in res)


def test_formatear_flujo_paralelo_acepta_generador():
    """formatear_flujo_ruts también debe aceptar generadores en modo paralelo."""
    resultados = list(formatear_flujo_ruts(_muestra(30), paralelo=True))
    assert len(resultados) == 30
    assert all(es_valido for es_valido, _ in resultados)


def test_formatear_flujo_paralelo_igual_que_serial():
    """formatear_flujo_ruts: modo paralelo == serial en valores formateados."""
    datos = list(_muestra(40))
    serial = [(ok, v) for ok, v in formatear_flujo_ruts(datos, paralelo=False)]
    paralelo = [(ok, v) for ok, v in formatear_flujo_ruts(datos, paralelo=True)]
    assert serial == paralelo
