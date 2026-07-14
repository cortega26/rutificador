"""Benchmarks del núcleo de rendimiento de Rutificador.

Cubre los caminos críticos de la API: parseo, validación de DV, procesamiento
por lotes y streaming. Cada benchmark usa datos deterministas y mide solo la
operación objetivo.
"""

from typing import List

from rutificador import (
    Rut,
    calcular_digito_verificador,
    evaluar_rendimiento,
    validar_flujo_ruts,
)
from rutificador.config import RigorValidacion
from rutificador.procesador import ProcesadorLotesRut

RUT_VALIDO = "12.345.678-5"
RUT_INVALIDO = "12.345.678-9"
RUT_FORMATO_ALTERNATIVO = "12 345 678-5"

_LOTE: List[str] = []
_BASES: List[str] = []


def _generar_lote(tamano: int = 1000) -> List[str]:
    global _LOTE  # noqa: PLW0603
    if len(_LOTE) >= tamano:
        return _LOTE[:tamano]
    _LOTE = []
    _bases = []
    for i in range(1_000_000, 1_000_000 + tamano):
        base = str(i)
        dv = calcular_digito_verificador(base)
        _LOTE.append(f"{base}-{dv}")
        _bases.append(base)
    return _LOTE


# ---------------------------------------------------------------------------
# Benchmarks de parseo y validación
# ---------------------------------------------------------------------------


def test_benchmark_parse_valido(benchmark):
    """Rut.parse() con entrada canónica válida."""
    resultado = benchmark(Rut.parse, RUT_VALIDO)
    assert resultado.estado == "valido"


def test_benchmark_parse_invalido(benchmark):
    """Rut.parse() con DV incorrecto."""
    resultado = benchmark(Rut.parse, RUT_INVALIDO)
    assert resultado.estado == "invalido"


def test_benchmark_parse_flexible(benchmark):
    """Rut.parse() en modo FLEXIBLE con formato alternativo."""
    resultado = benchmark(
        Rut.parse, RUT_FORMATO_ALTERNATIVO, modo=RigorValidacion.FLEXIBLE
    )
    assert resultado.estado == "valido"


def test_benchmark_calcular_dv(benchmark):
    """Cálculo puro del dígito verificador."""
    dv = benchmark(calcular_digito_verificador, "12345678")
    assert dv == "5"


# ---------------------------------------------------------------------------
# Benchmarks del constructor (builder)
# ---------------------------------------------------------------------------


def test_benchmark_constructor_valido(benchmark):
    """Rut() con entrada válida — camino completo del builder."""
    rut = benchmark(Rut, RUT_VALIDO)
    assert str(rut) == "12345678-5"


def test_benchmark_constructor_sin_dv(benchmark):
    """Rut() sin DV — calcula automáticamente."""
    rut = benchmark(Rut, "12345678")
    assert str(rut) == "12345678-5"


def test_benchmark_formatear(benchmark):
    """Rut.formatear() con todas las opciones."""
    rut = Rut(RUT_VALIDO)

    def _fmt():
        return rut.formatear(separador_miles=True, mayusculas=True)

    resultado = benchmark(_fmt)
    assert resultado == "12.345.678-5"


# ---------------------------------------------------------------------------
# Benchmarks de procesamiento por lotes
# ---------------------------------------------------------------------------


def test_benchmark_lote_serial_1000(benchmark):
    """ProcesadorLotesRut serial con 1000 RUTs válidos."""
    lote = _generar_lote(1000)
    procesador = ProcesadorLotesRut()

    def _validar():
        return procesador.validar_lista_ruts(lote, paralelo=False)

    resultado = benchmark(_validar)
    assert resultado.tasa_exito == 100.0


def test_benchmark_lote_paralelo_process_1000(benchmark):
    """ProcesadorLotesRut paralelo (ProcessPoolExecutor) con 1000 RUTs."""
    lote = _generar_lote(1000)
    procesador = ProcesadorLotesRut(motor_paralelo="process")

    def _validar():
        return procesador.validar_lista_ruts(lote, paralelo=True)

    resultado = benchmark(_validar)
    assert resultado.tasa_exito == 100.0


def test_benchmark_lote_paralelo_thread_1000(benchmark):
    """ProcesadorLotesRut paralelo (ThreadPoolExecutor) con 1000 RUTs."""
    lote = _generar_lote(1000)
    procesador = ProcesadorLotesRut(motor_paralelo="thread")

    def _validar():
        return procesador.validar_lista_ruts(lote, paralelo=True)

    resultado = benchmark(_validar)
    assert resultado.tasa_exito == 100.0


# ---------------------------------------------------------------------------
# Benchmarks de streaming
# ---------------------------------------------------------------------------


def test_benchmark_streaming_serial_1000(benchmark):
    """validar_flujo_ruts serial con 1000 RUTs."""
    lote = _generar_lote(1000)

    def _streaming():
        return list(validar_flujo_ruts(lote, paralelo=False))

    resultado = benchmark(_streaming)
    assert len(resultado) == 1000


def test_benchmark_streaming_paralelo_1000(benchmark):
    """validar_flujo_ruts paralelo con 1000 RUTs."""
    lote = _generar_lote(1000)

    def _streaming():
        return list(validar_flujo_ruts(lote, paralelo=True, motor_paralelo="thread"))

    resultado = benchmark(_streaming)
    assert len(resultado) == 1000


# ---------------------------------------------------------------------------
# Benchmarks de funcionalidades complementarias
# ---------------------------------------------------------------------------


def test_benchmark_normalizar(benchmark):
    """Rut.normalizar() con entrada canónica."""
    norm, errores, _ = benchmark(Rut.normalizar, RUT_VALIDO)
    assert norm == "12345678-5"
    assert not errores


def test_benchmark_enmascarar(benchmark):
    """Rut.enmascarar() con parámetros por defecto."""
    resultado = benchmark(Rut.enmascarar, RUT_VALIDO)
    assert resultado == "****5678-5"


def test_benchmark_rendimiento_e2e(benchmark):
    """evaluar_rendimiento() con 100 RUTs — smoke del pipeline completo."""
    resultado = benchmark(evaluar_rendimiento, num_ruts=100, paralelo=False)
    assert resultado["tasa_exito"] == 100.0
