"""Contratos machine-readable de salidas CLI y error 422 FastAPI.

Verifica que las salidas `--format json|jsonl` de la CLI y el detalle
de error 422 del contrib FastAPI cumplan los JSON Schemas versionados
en `schemas/`. Sigue el patrón de `tests/test_conformance_harness.py`
(`pytest.importorskip`, asserts directos).

Nota de disposición real: con `--format json`, stdout lleva solo el
array de ítems y el objeto metadata viaja a stderr (ver
`rutificador/cli.py`, estrategias `_EmisionJSON`/`_EmisionJSONL`).
"""

import json
import re
from pathlib import Path

import pytest

from rutificador import cli

RAIZ = Path(__file__).resolve().parent.parent
ESQUEMAS = RAIZ / "schemas"

_SEMVER = re.compile(r"^\d+\.\d+\.\d+$")


def _cargar_esquema(nombre: str) -> dict:
    return json.loads((ESQUEMAS / nombre).read_text(encoding="utf-8"))


def _subesquema(esquema: dict, nombre: str) -> dict:
    """Vista autocontenida de un `$def` para validar con `$ref`."""
    return {"$ref": f"#/$defs/{nombre}", "$defs": esquema["$defs"]}


def _extraer_json_final(texto: str) -> str:
    """Recorta el bloque JSON final de stderr tras las líneas de log."""
    lineas = texto.splitlines()
    for i, linea in enumerate(lineas):
        if linea.strip() == "{":
            return "\n".join(lineas[i:])
    raise AssertionError("stderr no contiene el objeto metadata JSON")


def test_schema_cli_valido_contra_metaschema():
    jsonschema = pytest.importorskip("jsonschema")
    for nombre in ("cli-salida.json", "fastapi-error-422.json"):
        esquema = _cargar_esquema(nombre)
        jsonschema.Draft202012Validator.check_schema(esquema)
        assert _SEMVER.fullmatch(esquema["version"]), nombre


def test_salida_json_conforme(tmp_path, capsys):
    jsonschema = pytest.importorskip("jsonschema")
    esquema = _cargar_esquema("cli-salida.json")
    archivo = tmp_path / "ruts.txt"
    archivo.write_text("12345678-5\n12345678-9\n", encoding="utf-8")
    codigo = cli.main(["validar", "--format", "json", str(archivo)])
    capturado = capsys.readouterr()
    assert codigo == 1
    items = json.loads(capturado.out)
    metadata = json.loads(_extraer_json_final(capturado.err))
    assert len(items) == 2
    jsonschema.validate(
        instance={"items": items, "metadata": metadata},
        schema=_subesquema(esquema, "salida_json"),
    )


def test_jsonl_linea_por_linea(tmp_path, capsys):
    jsonschema = pytest.importorskip("jsonschema")
    esquema = _cargar_esquema("cli-salida.json")
    esquema_item = _subesquema(esquema, "item")
    archivo = tmp_path / "ruts.txt"
    archivo.write_text("12345678-5\n12345678-9\n", encoding="utf-8")
    codigo = cli.main(["validar", "--format", "jsonl", str(archivo)])
    capturado = capsys.readouterr()
    assert codigo == 1
    lineas = [l for l in capturado.out.splitlines() if l.strip()]
    assert len(lineas) == 2
    for linea in lineas:
        jsonschema.validate(instance=json.loads(linea), schema=esquema_item)


def test_detalle_422_conforme():
    jsonschema = pytest.importorskip("jsonschema")
    pytest.importorskip("fastapi")
    from fastapi import Depends, FastAPI
    from fastapi.testclient import TestClient

    from rutificador.contrib.fastapi import ParametroRut
    from rutificador.rut import Rut

    app = FastAPI()

    @app.get("/validar")
    def validar_rut(rut: Rut = Depends(ParametroRut)):  # noqa: B008
        return {"valido": True}

    esquema = _cargar_esquema("fastapi-error-422.json")
    respuesta = TestClient(app).get("/validar", params={"rut": "12.345.678-k"})
    assert respuesta.status_code == 422
    cuerpo = respuesta.json()
    jsonschema.validate(instance=cuerpo, schema=esquema)
    jsonschema.validate(
        instance=cuerpo["detail"], schema=esquema["properties"]["detail"]
    )
    assert cuerpo["detail"][0]["loc"] == ["query", "rut"]
