#!/usr/bin/env python3
"""Script de migracion de imports obsoletos de rutificador v1.x a v2.0.

Uso:
    python scripts/migrate.py --check ruta/      # Escanea sin modificar
    python scripts/migrate.py --fix ruta/        # Reemplaza imports obsoletos
    python scripts/migrate.py --fix --dry-run ruta/  # Muestra cambios sin escribir

Reemplazos detectados:
    RutConfig -> ConfiguracionRut
    RutValidator -> ValidadorRut
    Validador (Protocol) -> ValidadorRut
    RutInvalidoError -> ErrorValidacionRut
    RutError -> ErrorRut
    RutValidationError -> ErrorValidacionRut
    RutFormatError -> ErrorFormatoRut
    RutDigitError -> ErrorDigitoRut
    RutLengthError -> ErrorLongitudRut
    RutProcessingError -> ErrorProcesamientoRut
    ConsultaRut -> consulta_rut
    ParametroRut -> parametro_rut
"""

import argparse
import ast
import sys
from pathlib import Path

REPLACEMENTS: dict[str, str] = {
    "RutConfig": "ConfiguracionRut",
    "RutValidator": "ValidadorRut",
    "Validador": "ValidadorRut",
    "RutInvalidoError": "ErrorValidacionRut",
    "RutError": "ErrorRut",
    "RutValidationError": "ErrorValidacionRut",
    "RutFormatError": "ErrorFormatoRut",
    "RutDigitError": "ErrorDigitoRut",
    "RutLengthError": "ErrorLongitudRut",
    "RutProcessingError": "ErrorProcesamientoRut",
    "ConsultaRut": "consulta_rut",
    "ParametroRut": "parametro_rut",
}

EXCLUDE_DIRS = {".git", ".venv", "__pycache__", ".mypy_cache", ".ruff_cache",
                ".pytest_cache", "node_modules", "dist", "site", "mutants",
                ".benchmarks", ".hypothesis", ".grimp_cache", ".import_linter_cache",
                ".codegraph", ".coverage"}


class ImportRewriter(ast.NodeTransformer):
    """AST transformer que renombra imports obsoletos."""

    def __init__(self):
        self.changes: list[tuple[int, str, str]] = []

    def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.AST:
        if node.names is None:
            return node
        new_names = []
        for alias in node.names:
            if alias.name in REPLACEMENTS:
                new_name = REPLACEMENTS[alias.name]
                self.changes.append((
                    node.lineno or 0,
                    alias.name,
                    new_name,
                ))
                new_names.append(ast.alias(name=new_name, asname=alias.asname))
            else:
                new_names.append(alias)
        node.names = new_names
        return node

    def visit_Name(self, node: ast.Name) -> ast.AST:
        """Renombra usos de simbolos obsoletos en el cuerpo del codigo."""
        if node.id in REPLACEMENTS:
            self.changes.append((
                node.lineno or 0,
                node.id,
                REPLACEMENTS[node.id],
            ))
            return ast.Name(id=REPLACEMENTS[node.id], ctx=node.ctx)
        return node


def scan_file(path: Path) -> list[dict]:
    """Escanea un archivo y retorna los cambios necesarios."""
    try:
        source = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return []

    tree = ast.parse(source, filename=str(path))
    rewriter = ImportRewriter()
    rewriter.visit(tree)

    results = []
    for lineno, old, new in rewriter.changes:
        results.append({
            "file": str(path),
            "line": lineno,
            "old": old,
            "new": new,
        })
    return results


def fix_file(path: Path, dry_run: bool = False) -> list[dict]:
    """Aplica los reemplazos a un archivo."""
    results = scan_file(path)
    if not results or dry_run:
        return results

    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    rewriter = ImportRewriter()
    new_tree = rewriter.visit(tree)
    ast.fix_missing_locations(new_tree)
    new_source = ast.unparse(new_tree)

    if new_source != source:
        path.write_text(new_source, encoding="utf-8")

    return results


def walk_python_files(root: Path) -> list[Path]:
    """Encuentra archivos .py recursivamente, excluyendo dirs ignorados."""
    files = []
    for path in root.rglob("*.py"):
        parts = set(path.parts)
        if parts & EXCLUDE_DIRS:
            continue
        if any(p.startswith(".") for p in path.parts if p not in (".", "..")):
            continue
        files.append(path)
    return files


def main():
    parser = argparse.ArgumentParser(
        description="Migra imports de rutificador v1.x a v2.0"
    )
    parser.add_argument(
        "path", nargs="?", default=".",
        help="Directorio o archivo a procesar"
    )
    parser.add_argument(
        "--check", action="store_true",
        help="Solo escanea, no modifica archivos"
    )
    parser.add_argument(
        "--fix", action="store_true",
        help="Aplica los reemplazos"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Muestra cambios sin escribir (requiere --fix)"
    )
    args = parser.parse_args()

    if not args.check and not args.fix:
        parser.error("Especifica --check o --fix")

    root = Path(args.path)
    if root.is_file():
        files = [root]
    else:
        files = walk_python_files(root)

    total_changes = 0
    files_changed = 0

    for fpath in sorted(files):
        if args.check or args.dry_run:
            results = scan_file(fpath)
            for r in results:
                total_changes += 1
                if r["file"] not in {str(f) for f in files[:files_changed]}:
                    files_changed += 1
                action = "[WOULD FIX]" if args.dry_run else "[FOUND]"
                print(f"{action} {r['file']}:{r['line']}  {r['old']} -> {r['new']}")
        elif args.fix:
            results = fix_file(fpath, dry_run=args.dry_run)
            for r in results:
                total_changes += 1
                print(f"[FIXED] {r['file']}:{r['line']}  {r['old']} -> {r['new']}")

    if total_changes == 0:
        print("No se encontraron imports obsoletos.")
    else:
        print(f"\n{total_changes} cambios en {files_changed} archivos.")

    return 0 if total_changes == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
