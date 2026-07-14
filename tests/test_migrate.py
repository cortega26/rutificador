"""Tests para el script de migracion de imports."""

import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"


def run_migrate(*args, cwd=None):
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "migrate.py")] + list(args),
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    return result


class TestMigrateScan:
    def test_detecta_import_obsoleto_en_archivo(self, tmp_path):
        f = tmp_path / "test.py"
        f.write_text("from rutificador import RutConfig\n")

        result = run_migrate("--check", str(tmp_path))
        assert result.returncode == 1
        assert "RutConfig" in result.stdout
        assert "ConfiguracionRut" in result.stdout

    def test_scan_limpio_sin_obsoletos(self, tmp_path):
        f = tmp_path / "test.py"
        f.write_text("from rutificador import ConfiguracionRut\n")

        result = run_migrate("--check", str(tmp_path))
        assert result.returncode == 0
        assert "No se encontraron" in result.stdout

    def test_detecta_import_from_obsoleto(self, tmp_path):
        f = tmp_path / "test.py"
        f.write_text("from rutificador.exceptions import RutInvalidoError\n")

        result = run_migrate("--check", str(tmp_path))
        assert result.returncode == 1
        assert "RutInvalidoError" in result.stdout
        assert "ErrorValidacionRut" in result.stdout

    def test_multiple_obsoletos(self, tmp_path):
        f = tmp_path / "test.py"
        f.write_text(
            "from rutificador import RutConfig, RutValidator\n"
            "from rutificador.exceptions import RutError\n"
        )

        result = run_migrate("--check", str(tmp_path))
        lines = result.stdout.strip().split("\n")
        assert len([l for l in lines if "FOUND" in l]) == 3

    def test_ignora_dirs_excluidos(self, tmp_path):
        (tmp_path / ".venv").mkdir()
        f = tmp_path / ".venv" / "test.py"
        f.write_text("from rutificador import RutConfig\n")

        result = run_migrate("--check", str(tmp_path))
        assert result.returncode == 0


class TestMigrateFix:
    def test_fix_reemplaza_import(self, tmp_path):
        f = tmp_path / "test.py"
        f.write_text("from rutificador import RutConfig\nprint(RutConfig)\n")

        result = run_migrate("--fix", str(tmp_path))
        assert result.returncode == 1

        content = f.read_text()
        assert "ConfiguracionRut" in content
        assert "RutConfig" not in content

    def test_fix_dry_run_no_escribe(self, tmp_path):
        f = tmp_path / "test.py"
        original = "from rutificador import RutConfig\n"
        f.write_text(original)

        result = run_migrate("--fix", "--dry-run", str(tmp_path))
        assert "WOULD FIX" in result.stdout

        assert f.read_text() == original

    def test_fix_no_toca_codigo_no_relacionado(self, tmp_path):
        f = tmp_path / "test.py"
        content = (
            "from rutificador import RutConfig\n"
            "import os\n"
            "x = 42\n"
            "def foo():\n"
            "    return 'hello'\n"
        )
        f.write_text(content)

        run_migrate("--fix", str(tmp_path))
        result = f.read_text()
        assert "import os" in result
        assert "x = 42" in result
        assert "def foo()" in result

    def test_fix_archivo_sin_cambios(self, tmp_path):
        f = tmp_path / "test.py"
        content = "import os\n"
        f.write_text(content)

        result = run_migrate("--fix", str(tmp_path))
        assert result.returncode == 0
        assert f.read_text() == content
