"""Pruebas para la interfaz de línea de comandos."""

import subprocess
import sys
import tracemalloc
from pathlib import Path
from typing import Optional

from rutificador import cli


def ejecutar_cli(
    *args: str, entrada: Optional[str] = None
) -> subprocess.CompletedProcess[str]:
    comando = [sys.executable, "-m", "rutificador.cli", *args]
    return subprocess.run(
        comando,
        input=entrada,
        capture_output=True,
        text=True,
        check=False,
        timeout=15,  # Anti-cuelgue
    )


def test_validar_desde_stdin():
    entrada = "12345678-5\n12345678-9\n"
    resultado = ejecutar_cli("validar", entrada=entrada)
    assert "12345678-5" in resultado.stdout
    assert "12345678-9" in resultado.stderr
    assert "[DV_DISCORDANTE]" in resultado.stderr
    assert "¿Quisiste decir 12345678-5?" in resultado.stderr
    assert resultado.returncode == 1


def test_formatear_desde_archivo(tmp_path: Path):
    archivo = tmp_path / "ruts.txt"
    archivo.write_text("12345678-5\n", encoding="utf-8")
    resultado = ejecutar_cli("formatear", str(archivo), "--separador-miles")
    assert "12.345.678-5" in resultado.stdout
    assert resultado.returncode == 0


def test_memoria_validar_archivo_grande(tmp_path: Path, monkeypatch):
    archivo = tmp_path / "ruts.txt"
    # Reducimos a 10k para mayor estabilidad en el entorno de pruebas
    archivo.write_text("12345678-5\n" * 10_000, encoding="utf-8")

    def _consumir(
        ruts, paralelo=False, max_trabajadores=None, motor_paralelo="process"
    ):
        del paralelo, max_trabajadores, motor_paralelo
        for _ in ruts:
            pass
        return iter([])

    monkeypatch.setattr(cli, "validar_flujo_ruts", _consumir)

    tracemalloc.start()
    codigo_salida = cli.main(["validar", str(archivo)])
    _, pico = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert codigo_salida == 0
    assert pico < 20 * 1024 * 1024


def test_memoria_formatear_archivo_grande(tmp_path: Path, monkeypatch):
    archivo = tmp_path / "ruts.txt"
    # Reducimos a 10k para mayor estabilidad en el entorno de pruebas
    archivo.write_text("12345678-5\n" * 10_000, encoding="utf-8")

    def _consumir(
        ruts,
        separador_miles=False,
        mayusculas=False,
        paralelo=False,
        max_trabajadores=None,
        motor_paralelo="process",
    ):
        del separador_miles, mayusculas, paralelo, max_trabajadores, motor_paralelo
        for _ in ruts:
            pass
        return iter([])

    monkeypatch.setattr(cli, "formatear_flujo_ruts", _consumir)

    tracemalloc.start()
    codigo_salida = cli.main(["formatear", str(archivo)])
    _, pico = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert codigo_salida == 0
    assert pico < 20 * 1024 * 1024


def test_cli_mejorar_flag():
    # RUT con DV erróneo pero mejorable de forma unívoca (dist 1 única)
    entrada = "12345678-1\n"
    # Sin --mejorar, falla
    res1 = ejecutar_cli("validar", entrada=entrada)
    assert res1.returncode == 1

    # Con --mejorar, pasa y se corrige
    res2 = ejecutar_cli("validar", "--mejorar", entrada=entrada)
    assert res2.returncode == 0
    assert "12345678-5" in res2.stdout


def test_cli_jsonl_format():
    entrada = "12345678-5\n12.345.678-k\n"
    resultado = ejecutar_cli("validar", "--format", "jsonl", entrada=entrada)
    lineas = resultado.stdout.strip().split("\n")
    # 2 registros + 1 metadata = 3 líneas
    assert len(lineas) == 3
    import json

    data_reg1 = json.loads(lineas[0])
    assert data_reg1["valido"] is True
    data_meta = json.loads(lineas[2])
    assert "audit" in data_meta


def test_cli_paralelo():
    entrada = "12345678-5\n" * 10
    resultado = ejecutar_cli("validar", "--paralelo", entrada=entrada)
    assert resultado.returncode == 0
    assert "12345678-5" in resultado.stdout
