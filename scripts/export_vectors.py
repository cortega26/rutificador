#!/usr/bin/env python3
"""Exporta los test vectors canonicos a formatos alternativos.

Uso:
    python scripts/export_vectors.py --format json  # JSON plano
    python scripts/export_vectors.py --format yaml  # YAML
    python scripts/export_vectors.py --all          # todos los formatos
"""

import json
import sys
from pathlib import Path


VECTORS_DIR = Path(__file__).resolve().parent.parent / "tests" / "vectors"


def export_json(vectors, output_dir):
    path = output_dir / "conformance.json"
    path.write_text(json.dumps(vectors, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  JSON -> {path}")


def export_yaml(vectors, output_dir):
    try:
        import yaml
    except ImportError:
        print("  YAML: PyYAML no instalado. Saltando.")
        return
    path = output_dir / "conformance.yaml"
    path.write_text(
        yaml.dump(vectors, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    print(f"  YAML -> {path}")


def main():
    source = VECTORS_DIR / "conformance.json"
    if not source.exists():
        print(f"Error: archivo fuente no encontrado: {source}")
        return 1

    with open(source, encoding="utf-8") as f:
        vectors = json.load(f)

    output_dir = Path("dist/vectors")
    output_dir.mkdir(parents=True, exist_ok=True)

    if len(sys.argv) < 2 or "--all" in sys.argv:
        export_json(vectors, output_dir)
        export_yaml(vectors, output_dir)
    elif "--format" in sys.argv:
        fmt_idx = sys.argv.index("--format")
        if fmt_idx + 1 < len(sys.argv):
            fmt = sys.argv[fmt_idx + 1]
            if fmt == "json":
                export_json(vectors, output_dir)
            elif fmt == "yaml":
                export_yaml(vectors, output_dir)
            else:
                print(f"Formato desconocido: {fmt}")
                return 1
        else:
            print("Especifica un formato: json, yaml")
            return 1
    else:
        print("Uso: export_vectors.py --format json|yaml|--all")
        return 1

    print(f"\nVectors exportados a {output_dir}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
