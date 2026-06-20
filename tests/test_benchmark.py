"""Pruebas funcionales de la infraestructura de benchmarking."""

from typing import Any

from rutificador import Rut


def test_benchmark_parse_rut(benchmark: Any) -> None:
    """Comprueba que pytest-benchmark mide el camino principal de parseo."""
    resultado = benchmark(Rut.parse, "12.345.678-5")

    assert resultado.estado == "valido"
    assert resultado.normalizado == "12345678-5"
