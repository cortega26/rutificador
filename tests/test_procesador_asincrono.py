"""Pruebas para las funciones asíncronas del procesador de RUTs."""

from typing import AsyncIterator, List, Tuple, Union

import pytest

from rutificador import (
    DetalleError,
    async_formatear_lista_ruts,
    async_formatear_stream_ruts,
    async_validar_lista_ruts,
    async_validar_stream_ruts,
)


@pytest.mark.asyncio
async def test_async_validar_lista_ruts():
    """Verifica que la validación asíncrona separe RUTs válidos e inválidos."""

    ruts = ["12.345.678-5", "98765432-1", "1-9"]

    resultado = await async_validar_lista_ruts(ruts)

    assert len(resultado["validos"]) == 2
    assert "12345678-5" in resultado["validos"]
    assert "1-9" in resultado["validos"]
    assert len(resultado["invalidos"]) == 1
    detalle_error = resultado["invalidos"][0]
    assert isinstance(detalle_error, DetalleError)
    assert detalle_error.rut == "98765432-1"


@pytest.mark.asyncio
async def test_async_formatear_lista_ruts():
    """Comprueba que el formateo asíncrono conserve el reporte esperado."""

    ruts = ["12.345.678-5", "98765432-1", "1-9"]

    reporte = await async_formatear_lista_ruts(
        ruts,
        separador_miles=True,
        mayusculas=True,
    )

    assert "RUTs válidos:" in reporte
    assert "12.345.678-5" in reporte
    assert "1-9" in reporte
    assert "RUTs inválidos:" in reporte
    assert "98765432-1" in reporte


async def _generar_ruts(ruts: List[str]) -> AsyncIterator[str]:
    """Generador auxiliar para simular flujos asíncronos."""

    for rut in ruts:
        yield rut


@pytest.mark.asyncio
async def test_async_validar_stream_ruts():
    """Valida que el flujo asíncrono preserve el orden y los tipos de salida."""

    ruts = ["12.345.678-5", "98765432-1"]

    resultados: List[Tuple[bool, Union[str, DetalleError]]] = []
    async for es_valido, valor in async_validar_stream_ruts(_generar_ruts(ruts)):
        resultados.append((es_valido, valor))

    assert len(resultados) == 2
    assert resultados[0][0] is True
    assert resultados[0][1] == "12345678-5"
    assert resultados[1][0] is False
    assert isinstance(resultados[1][1], DetalleError)
    assert resultados[1][1].rut == "98765432-1"


@pytest.mark.asyncio
async def test_async_formatear_stream_ruts():
    """Comprueba la salida del formateador asíncrono sobre un flujo mixto."""

    ruts = ["12.345.678-5", "98765432-1", "1-9"]

    resultados: List[Tuple[bool, Union[str, DetalleError]]] = []
    async for es_valido, valor in async_formatear_stream_ruts(
        _generar_ruts(ruts), separador_miles=True, mayusculas=True
    ):
        resultados.append((es_valido, valor))

    assert len(resultados) == 3
    assert resultados[0][0] is True
    assert resultados[0][1] == "12.345.678-5"
    assert resultados[1][0] is False
    assert isinstance(resultados[1][1], DetalleError)
    assert resultados[2][0] is True
    assert resultados[2][1] == "1-9"
