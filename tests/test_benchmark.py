"""Pruebas funcionales de la infraestructura de benchmarking."""

from typing import Any

from rutificador import Rut


def test_benchmark_parse_rut(benchmark: Any) -> None:
    """Comprueba que pytest-benchmark mide el camino principal de parseo."""
    resultado = benchmark(Rut.parse, "12.345.678-5")

    if resultado.estado != "valido":
        raise AssertionError(f"Estado inesperado: {resultado.estado}")
    if resultado.normalizado != "12345678-5":
        raise AssertionError(f"Normalización inesperada: {resultado.normalizado}")
