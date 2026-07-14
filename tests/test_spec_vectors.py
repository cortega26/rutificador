"""Verifica que la implementacion actual cumple la especificacion formal.

Los test vectors en tests/vectors/conformance.json son la fuente canonica
de verdad. Este modulo los valida contra la implementacion de rutificador.

Los archivos legacy (test_vectors_dv.json, test_vectors_validacion.json)
se mantienen como referencia historica; conformance.json es la fuente
unificada y versionada.
"""

import json
from pathlib import Path

import pytest

from rutificador import Rut, RigorValidacion
from rutificador.utils import calcular_digito_verificador

VECTORS_DIR = Path(__file__).parent / "vectors"


@pytest.fixture(scope="module")
def vectores_conformidad():
    with open(VECTORS_DIR / "conformance.json", encoding="utf-8") as f:
        return json.load(f)


class TestVectoresDigitoVerificador:
    @pytest.mark.parametrize(
        "caso",
        json.loads(
            (VECTORS_DIR / "conformance.json")
            .read_text(encoding="utf-8")
        )["casos_dv"],
        ids=lambda c: f"base={c['base']}",
    )
    def test_dv(self, caso):
        assert calcular_digito_verificador(caso["base"]) == caso["dv_esperado"]


class TestVectoresValidacion:
    @pytest.mark.parametrize(
        "caso",
        json.loads(
            (VECTORS_DIR / "conformance.json")
            .read_text(encoding="utf-8")
        )["casos_validacion"],
        ids=lambda c: f"{c['entrada'][:20]} [{c['modo']}]",
    )
    def test_validacion(self, caso):
        modo = (
            RigorValidacion.ESTRICTO
            if caso["modo"] == "estricto"
            else RigorValidacion.FLEXIBLE
        )
        resultado = Rut.parse(caso["entrada"], modo=modo)

        assert resultado.estado == caso["estado_esperado"]

        if "normalizado" in caso:
            assert resultado.normalizado == caso["normalizado"]

        if "codigo_error" in caso:
            codigos = [e.codigo for e in resultado.errores]
            assert caso["codigo_error"] in codigos, (
                f"Esperado {caso['codigo_error']} en {codigos}"
            )
