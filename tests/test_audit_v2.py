import json
import subprocess
import sys

from pydantic import BaseModel

from rutificador.contrib.pydantic.rutstr import RutStr, RutStrAnnotated


def ejecutar_cli(*args):
    """Ejecuta el comando CLI y devuelve el resultado."""
    comando = [sys.executable, "-m", "rutificador.cli", *args]
    return subprocess.run(comando, capture_output=True, text=True, check=False)


def test_cli_info_text():
    res = ejecutar_cli("info")
    assert res.returncode == 0
    assert "--- RUTIFICADOR v1.4.5 ---" in res.stdout
    assert "Descripción:" in res.stdout
    assert "Python" in res.stdout


def test_cli_info_json():
    res = ejecutar_cli("info", "--format", "json")
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["version"] == "1.4.5"
    assert "funcionalidades" in data


def test_pydantic_rutstr_formatos():
    """Prueba los diferentes formatos de RutStr en modelos Pydantic."""

    # Tipo por defecto (base-dv)
    class ModelBase(BaseModel):
        """Modelo base."""

        rut: RutStr

    m1 = ModelBase(rut="12.345.678-5")
    assert m1.rut == "12345678-5"

    # Formato miles
    RutMiles = RutStrAnnotated(formato="miles")

    class ModelMiles(BaseModel):
        """Modelo con formato miles."""

        rut: RutMiles

    m2 = ModelMiles(rut="12345678-5")
    assert m2.rut == "12.345.678-5"

    # Formato canonico (mayúsculas)
    RutCanon = RutStrAnnotated(formato="canonico")

    class ModelCanon(BaseModel):
        """Modelo con formato canónico."""

        rut: RutCanon

    m3 = ModelCanon(rut="84920968-k")
    assert m3.rut == "84920968-K"

    # Formato miles-con-guion (mayúsculas + puntos)
    RutFull = RutStrAnnotated(formato="miles-con-guion")

    class ModelFull(BaseModel):
        """Modelo con formato completo."""

        rut: RutFull

    m4 = ModelFull(rut="84920968-k")
    assert m4.rut == "84.920.968-K"
