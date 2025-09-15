import pytest

from rutificador import (
    normalizar_base_rut,
    obtener_informacion_version,
    monitor_de_rendimiento,
    formatear_lista_ruts as formatear_lista_ruts_global,
    formatear_stream_ruts as formatear_stream_ruts_global,
    validar_lista_ruts as validar_lista_ruts_global,
    validar_stream_ruts as validar_stream_ruts_global,
    configurar_registro,
    evaluar_rendimiento,
    Rut,
    calcular_digito_verificador,
    DetalleError,
    __version__,
)
from rutificador.formatter import FormateadorCSV
from rutificador.exceptions import ErrorValidacionRut


def test_normalizar_base_rut():
    assert normalizar_base_rut("12.345.678") == "12345678"
    assert normalizar_base_rut("000001") == "1"


def test_calcular_digito_verificador_invalid_inputs():
    with pytest.raises(ErrorValidacionRut):
        calcular_digito_verificador("ABC123")
    with pytest.raises(ErrorValidacionRut):
        calcular_digito_verificador(12345678)  # type: ignore[arg-type]


def test_normalizar_base_rut_invalid_type():
    with pytest.raises(ErrorValidacionRut):
        normalizar_base_rut(123)  # type: ignore[arg-type]


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
    assert any(
        isinstance(detalle, DetalleError) and "invalid" in detalle.rut
        for detalle in resultado_validacion["invalidos"]
    )

    texto = formatear_lista_ruts_global(ruts, formato="csv")
    assert "rut" in texto
    assert "12345678-5" in texto


def test_validar_stream_ruts_con_generador():
    ruts = (r for r in ["12345678-5", "12345679-3", "12345678-9"])
    resultados = list(validar_stream_ruts_global(ruts))
    assert resultados[0] == (True, "12345678-5")
    assert resultados[1] == (True, "12345679-3")
    assert resultados[2][0] is False
    assert isinstance(resultados[2][1], DetalleError)
    assert resultados[2][1].rut == "12345678-9"
    assert resultados[2][1].codigo == "DIGIT_ERROR"


def test_formatear_stream_ruts_con_generador():
    ruts = (r for r in ["12345678-5", "12345679-3", "12345678-9"])
    resultados = list(formatear_stream_ruts_global(ruts, separador_miles=True))
    assert resultados[0] == (True, "12.345.678-5")
    assert resultados[1] == (True, "12.345.679-3")
    assert resultados[2][0] is False
    assert isinstance(resultados[2][1], DetalleError)
    assert resultados[2][1].rut == "12345678-9"
    assert resultados[2][1].codigo == "DIGIT_ERROR"


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
