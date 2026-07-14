#!/usr/bin/env python3
"""Compara dos archivos JSON de pytest-benchmark y reporta regresiones.

Uso:
    python scripts/compare_benchmarks.py base.json head.json [--threshold 20]

El umbral (threshold) es el porcentaje de degradación que se considera
regresión. Por defecto 20 %. Si alguna operación es >= umbral % más lenta
en head que en base, el script termina con código de salida 2 (degradación
detectada). Si es más rápida, termina con 0.

Formato de salida: tabla markdown con nombre, media base, media head,
diferencia porcentual y veredicto.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict


def _nombre_legible(nombre_completo: str) -> str:
    return nombre_completo.replace("tests/benchmarks/test_benchmarks_core.py::", "")


def _cargar_benchmarks(ruta: Path) -> Dict[str, float]:
    with open(ruta, encoding="utf-8") as f:
        datos: Dict[str, Any] = json.load(f)
    medias: Dict[str, float] = {}
    for bench in datos.get("benchmarks", []):
        nombre = bench.get("name", "")
        stats = bench.get("stats", {})
        media = stats.get("mean")
        if nombre and media is not None:
            medias[nombre] = float(media)
    return medias


def comparar(ruta_base: Path, ruta_head: Path, umbral: float = 20.0) -> int:
    base = _cargar_benchmarks(ruta_base)
    head = _cargar_benchmarks(ruta_head)

    nombres = sorted(set(base) | set(head))
    if not nombres:
        print("| No se encontraron benchmarks para comparar |")
        return 0

    regresiones = 0
    lineas: list[str] = []
    lineas.append("| Benchmark | Base (s) | Head (s) | Δ% | Veredicto |")
    lineas.append("|---|---|---|---|---|")

    for nombre in nombres:
        media_base = base.get(nombre)
        media_head = head.get(nombre)
        legible = _nombre_legible(nombre)

        if media_base is None:
            lineas.append(f"| {legible} | — | {media_head:.6f} | nuevo | — |")
            continue
        if media_head is None:
            lineas.append(f"| {legible} | {media_base:.6f} | — | eliminado | — |")
            continue

        if media_base == 0:
            delta = 0.0
        else:
            delta = ((media_head - media_base) / media_base) * 100.0

        if delta >= umbral:
            veredicto = "REGRESION"
            regresiones += 1
        elif delta <= -umbral:
            veredicto = "mejora"
        else:
            veredicto = "ok"

        lineas.append(
            f"| {legible} | {media_base:.6f} | {media_head:.6f} | {delta:+.1f}% | {veredicto} |"
        )

    summary = "\n".join(lineas)
    print(summary)

    if regresiones:
        print(f"\nSe detectaron {regresiones} regresiones (umbral: ≥{umbral:.0f}%).")
        return 2

    print(f"\nSin regresiones detectadas (umbral: ≥{umbral:.0f}%).")
    return 0


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Compara resultados de pytest-benchmark y detecta regresiones"
    )
    parser.add_argument("base", type=Path, help="Archivo JSON de la línea base")
    parser.add_argument("head", type=Path, help="Archivo JSON del PR/rama actual")
    parser.add_argument(
        "--threshold",
        type=float,
        default=20.0,
        help="Porcentaje de degradación que se considera regresión (default: 20)",
    )
    args = parser.parse_args()

    if not args.base.exists():
        print(f"Error: archivo base no encontrado: {args.base}", file=sys.stderr)
        return 1
    if not args.head.exists():
        print(f"Error: archivo head no encontrado: {args.head}", file=sys.stderr)
        return 1

    return comparar(args.base, args.head, args.threshold)


if __name__ == "__main__":
    sys.exit(main())
