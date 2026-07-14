#!/usr/bin/env python3
"""Harness de conformidad para implementaciones de validador de RUT chileno.

Uso:
    python scripts/conformance.py
    python scripts/conformance.py --vectors path/to/conformance.json

El script carga los test vectors canonicos y verifica que la implementacion
local produce los resultados esperados para cada caso.

Exit code 0 = todos los casos pasan. Exit code 1 = hay fallos.
"""

import json
import sys
from pathlib import Path


# --- Seccion de adaptacion para implementaciones externas ---
# Para usar con otra implementacion, reemplaza estas funciones.


def dv_implementation(base: str, config: dict) -> str:
    """Calcula el digito verificador para una base numerica."""
    from rutificador.utils import calcular_digito_verificador

    return calcular_digito_verificador(base)


def validation_implementation(entrada: str, modo: str, config: dict) -> dict:
    """Valida una entrada y retorna {estado, normalizado, codigos_error}."""
    from rutificador import Rut, RigorValidacion

    modo_enum = (
        RigorValidacion.ESTRICTO if modo == "estricto" else RigorValidacion.FLEXIBLE
    )
    resultado = Rut.parse(entrada, modo=modo_enum)
    return {
        "estado": resultado.estado,
        "normalizado": resultado.normalizado,
        "codigos_error": [e.codigo for e in resultado.errores],
    }


# --- Fin de seccion de adaptacion ---


def run_conformance(vectors_path: Path) -> int:
    with open(vectors_path, encoding="utf-8") as f:
        vectors = json.load(f)

    config = vectors["configuracion"]
    failures = 0
    total = 0

    print(f"Vectors v{vectors['version']} (spec v{vectors['spec_version']})")
    print(f"Algoritmo: {vectors['algoritmo']['nombre']}")
    print()

    # Casos de DV
    print("--- Calculo de Digito Verificador ---")
    for caso in vectors["casos_dv"]:
        total += 1
        result = dv_implementation(caso["base"], config)
        expected = caso["dv_esperado"].lower()
        status = "PASS" if result.lower() == expected else "FAIL"
        if status == "FAIL":
            failures += 1
        print(
            f"  [{status}] base={caso['base']:>10}  esperado={expected}  "
            f"obtenido={result}"
        )

    # Casos de validacion
    print("\n--- Validacion de RUT ---")
    for caso in vectors["casos_validacion"]:
        total += 1
        result = validation_implementation(caso["entrada"], caso["modo"], config)

        estado_ok = result["estado"] == caso["estado_esperado"]
        codigo_ok = True
        if "codigo_error" in caso:
            codigo_ok = caso["codigo_error"] in result.get("codigos_error", [])
        normalizado_ok = True
        if "normalizado" in caso:
            normalizado_ok = result.get("normalizado") == caso["normalizado"]

        status = "PASS" if (estado_ok and codigo_ok and normalizado_ok) else "FAIL"
        if status == "FAIL":
            failures += 1
            detalles = []
            if not estado_ok:
                detalles.append(
                    f"estado={result['estado']} (esperado={caso['estado_esperado']})"
                )
            if not codigo_ok:
                detalles.append(
                    f"codigos_error={result.get('codigos_error', [])} "
                    f"(esperado contiene {caso.get('codigo_error')})"
                )
            if not normalizado_ok:
                detalles.append(
                    f"normalizado={result.get('normalizado')} "
                    f"(esperado={caso.get('normalizado')})"
                )
        print(
            f"  [{status}] entrada='{caso['entrada']}'  modo={caso['modo']}  "
            f"estado={result['estado']}"
        )
        if status == "FAIL":
            for d in detalles:
                print(f"         -> {d}")

    print(f"\n{'=' * 50}")
    print(f"Resultado: {total - failures}/{total} pasaron")
    if failures:
        print(f"  {failures} FALLOS")
    return 0 if failures == 0 else 1


def main():
    default = (
        Path(__file__).resolve().parent.parent
        / "tests"
        / "vectors"
        / "conformance.json"
    )
    vectors_path = default
    if len(sys.argv) > 2 and sys.argv[1] == "--vectors":
        vectors_path = Path(sys.argv[2])
    elif len(sys.argv) > 1:
        vectors_path = Path(sys.argv[1])

    if not vectors_path.exists():
        print(f"Error: archivo de vectores no encontrado: {vectors_path}")
        return 1

    return run_conformance(vectors_path)


if __name__ == "__main__":
    sys.exit(main())
