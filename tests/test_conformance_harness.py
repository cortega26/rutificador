"""Verifica el harness de conformidad como artefacto publicable.

Cubre lo que `tests/test_spec_vectors.py` no cubre: que
`tests/vectors/conformance.json` sea valido contra
`tests/vectors/schema.json`, que el runner standalone
(`scripts/conformance.py`) pase con la implementacion propia, que su
interfaz de adaptacion cargue una segunda implementacion (mock), y que
el exportador genere el artefacto versionado en `dist/vectors/`.
"""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
VECTORES = RAIZ / "tests" / "vectors"
CONFORMANCE = VECTORES / "conformance.json"


def _cargar_script(nombre: str):
    """Carga un script de `scripts/` como modulo sin instalar nada."""
    ruta = RAIZ / "scripts" / nombre
    spec = importlib.util.spec_from_file_location(f"harness_{ruta.stem}", ruta)
    assert spec is not None and spec.loader is not None
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def test_vectores_validos_contra_schema():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads((VECTORES / "schema.json").read_text(encoding="utf-8"))
    datos = json.loads(CONFORMANCE.read_text(encoding="utf-8"))
    jsonschema.validate(instance=datos, schema=schema)
    assert datos["version"] and datos["spec_version"]
    assert len(datos["casos_dv"]) >= 10
    assert len(datos["casos_validacion"]) >= 12


def test_runner_pasa_implementacion_propia(capsys):
    runner = _cargar_script("conformance.py")
    assert runner.run_conformance(CONFORMANCE) == 0
    capsys.readouterr()


def test_runner_acepta_segunda_implementacion(capsys, monkeypatch):
    """La interfaz de adaptacion carga un mock: stub correcto -> 0."""
    runner = _cargar_script("conformance.py")
    datos = json.loads(CONFORMANCE.read_text(encoding="utf-8"))
    dv_esperados = {c["base"]: c["dv_esperado"].lower() for c in datos["casos_dv"]}
    casos = {(c["entrada"], c["modo"]): c for c in datos["casos_validacion"]}

    def dv_mock(base, config):
        return dv_esperados[base]

    def validacion_mock(entrada, modo, config):
        caso = casos[(entrada, modo)]
        return {
            "estado": caso["estado_esperado"],
            "normalizado": caso.get("normalizado"),
            "codigos_error": ([caso["codigo_error"]] if "codigo_error" in caso else []),
        }

    monkeypatch.setattr(runner, "dv_implementation", dv_mock)
    monkeypatch.setattr(runner, "validation_implementation", validacion_mock)
    assert runner.run_conformance(CONFORMANCE) == 0
    capsys.readouterr()


def test_runner_reprueba_stub_roto(capsys, monkeypatch):
    """Un stub que siempre responde mal debe producir exit code 1."""
    runner = _cargar_script("conformance.py")
    monkeypatch.setattr(runner, "dv_implementation", lambda b, c: "X")
    monkeypatch.setattr(
        runner,
        "validation_implementation",
        lambda e, m, c: {
            "estado": "nunca",
            "normalizado": None,
            "codigos_error": [],
        },
    )
    assert runner.run_conformance(CONFORMANCE) == 1
    capsys.readouterr()


def test_exportador_genera_artefacto(tmp_path, monkeypatch):
    exportador = _cargar_script("export_vectors.py")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["export_vectors.py", "--all"])
    assert exportador.main() == 0
    artefacto = tmp_path / "dist" / "vectors" / "conformance.json"
    assert artefacto.exists()
    assert json.loads(artefacto.read_text(encoding="utf-8")) == json.loads(
        CONFORMANCE.read_text(encoding="utf-8")
    )
