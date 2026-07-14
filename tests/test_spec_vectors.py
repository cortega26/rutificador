"""Verifica que la implementación actual cumple la especificación formal.

Los test vectors en tests/vectors/ son la fuente canónica de verdad.
Este módulo los valida contra la implementación de rutificador.
"""

import json
from pathlib import Path

import pytest

from rutificador import Rut, RigorValidacion
from rutificador.utils import calcular_digito_verificador

VECTORS_DIR = Path(__file__).parent / "vectors"


def _cargar_vectors(nombre: str):
    with open(VECTORS_DIR / nombre, encoding="utf-8") as f:
        return json.load(f)


class TestVectoresDigitoVerificador:
    @pytest.mark.parametrize(
        "caso",
        _cargar_vectors("test_vectors_dv.json")["casos"],
        ids=lambda c: f"base={c['base']}",
    )
    def test_dv(self, caso):
        assert calcular_digito_verificador(caso["base"]) == caso["dv_esperado"]


class TestVectoresValidacion:
    @pytest.mark.parametrize(
        "caso",
        _cargar_vectors("test_vectors_validacion.json")["casos"],
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
