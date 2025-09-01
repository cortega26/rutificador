import pytest

from rutificador.main import (
    normalizar_base_rut,
    obtener_informacion_version,
    monitor_de_rendimiento,
    formatear_lista_ruts as formatear_lista_ruts_global,
    validar_lista_ruts as validar_lista_ruts_global,
    configurar_registro,
    evaluar_rendimiento,
    Rut,
)
from rutificador import __version__
from rutificador.formatter import FormateadorCSV


def test_normalizar_base_rut():
    assert normalizar_base_rut("12.345.678") == "12345678"
    assert normalizar_base_rut("000001") == "1"


def test_obtener_informacion_version():
    info = obtener_informacion_version()
    assert info["version"] == __version__
    assert "features" in info


def test_rut_cache_management():
    Rut.limpiar_cache()
    stats = Rut.estadisticas_cache()
    assert stats["cache_size"] == 0


def test_global_validar_y_formatear():
    ruts = ["12345678-5", "12345679-5", "invalid"]
    resultado_validacion = validar_lista_ruts_global(ruts)
    assert "12345678-5" in resultado_validacion["validos"]
    assert any("invalid" in tup[0] for tup in resultado_validacion["invalidos"])

    texto = formatear_lista_ruts_global(ruts, formato="csv")
    assert "rut" in texto
    assert "12345678-5" in texto


def test_configurar_registro():
    configurar_registro()


def test_evaluar_rendimiento():
    datos = evaluar_rendimiento(num_ruts=5, parallel=False)
    assert datos["test_ruts_count"] == 5
    assert "tasa_exito" in datos


def test_monitor_de_rendimiento_success_and_failure():
    @monitor_de_rendimiento
    def sample(x):
        return x * 2

    @monitor_de_rendimiento
    def sample_error():
        raise ValueError("boom")

    assert sample(3) == 6
    with pytest.raises(ValueError):
        sample_error()


def test_formateador_csv_previene_inyeccion():
    """El formateador CSV debe mitigar la inyección de fórmulas."""
    formatter = FormateadorCSV()
    contenido = formatter.formatear(["=2+2"])
    lineas = contenido.splitlines()
    assert lineas[1] == "'=2+2"
