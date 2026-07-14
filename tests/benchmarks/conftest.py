"""Configuración compartida de pytest-benchmark para la suite de benchmarks."""

import pytest


def pytest_benchmark_update_machine_info(config, machine_info):
    """Enriquece la metadata de la máquina para comparaciones entre runners."""



@pytest.fixture(scope="session")
def benchmark_session_fixture():
    """Fixture de sesión que asegura que los datos se generan una sola vez."""
