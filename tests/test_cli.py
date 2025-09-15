"""Pruebas para la interfaz de línea de comandos."""

import subprocess
import sys
from pathlib import Path
from typing import Optional


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
