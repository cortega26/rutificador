"""Pruebas para la interfaz de línea de comandos."""

import subprocess
import sys
import argparse
import tracemalloc
from pathlib import Path
from typing import Optional

import rutificador.cli as cli


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
    )


def test_validar_desde_stdin():
    entrada = "12345678-5\n12345678-9\n"
    resultado = ejecutar_cli("validar", entrada=entrada)
    assert "12345678-5" in resultado.stdout
    assert "12345678-9" in resultado.stderr
    assert resultado.returncode == 1


def test_formatear_desde_archivo(tmp_path: Path):
    archivo = tmp_path / "ruts.txt"
    archivo.write_text("12345678-5\n", encoding="utf-8")
    resultado = ejecutar_cli("formatear", str(archivo), "--separador-miles")
    assert "12.345.678-5" in resultado.stdout
    assert resultado.returncode == 0


def test_memoria_validar_archivo_grande(tmp_path: Path, monkeypatch):
    archivo = tmp_path / "ruts.txt"
    archivo.write_text("12345678-5\n" * 500_000, encoding="utf-8")

    def _consumir(ruts):
        for _ in ruts:
            pass
        return []

    monkeypatch.setattr(cli, "validar_stream_ruts", _consumir)

    args = argparse.Namespace(archivo=str(archivo))
    tracemalloc.start()
    cli._comando_validar(args)
    _, pico = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert pico < 20 * 1024 * 1024


def test_memoria_formatear_archivo_grande(tmp_path: Path, monkeypatch):
    archivo = tmp_path / "ruts.txt"
    archivo.write_text("12345678-5\n" * 500_000, encoding="utf-8")

    def _consumir(ruts, separador_miles, mayusculas):
        for _ in ruts:
            pass
        return []

    monkeypatch.setattr(cli, "formatear_stream_ruts", _consumir)

    args = argparse.Namespace(
        archivo=str(archivo), separador_miles=False, mayusculas=False
    )
    tracemalloc.start()
    cli._comando_formatear(args)
    _, pico = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert pico < 20 * 1024 * 1024
