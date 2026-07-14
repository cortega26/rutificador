# Plan 013: Ejecutar v2.0 — script de migración, limpieza de deprecaciones y guía

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 6b61e0e..HEAD -- rutificador/__init__.py rutificador/exceptions.py rutificador/config.py rutificador/validador.py pyproject.toml`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P1
- **Effort**: M
- **Risk**: MEDIUM
- **Depends on**: 014 (mypy strict) — strongly recommended before removing deprecated APIs, since strict typing will catch any remaining coupling
- **Category**: migration
- **Planned at**: commit `6b61e0e`, 2026-07-14

## Why this matters

rutificador has accumulated 15+ deprecated symbols since v1.4.4 — old class names like `RutInvalidoError`, `RutConfig`, `RutValidator` that emit `DeprecationWarning` on every access. v2.0 is the planned breaking release to remove them all, as documented in `ROADMAP.md:41-83`. The migration window is 6 months from the guide publication. The script `rutificador-migrate` is already promised in the ROADMAP but not yet built. Landing this plan now gives the ecosystem the full transition window before v2.0 ships.

## Current state

- `rutificador/__init__.py:64-68` — `_DEPRECATED_EXPORTS` maps `RutConfig → ConfiguracionRut`, `RutValidator → ValidadorRut`, `RutInvalidoError → ErrorValidacionRut`
- `rutificador/__init__.py:71-79` — `__getattr__` shim that emits `DeprecationWarning` for each deprecated export
- `rutificador/exceptions.py:117-125` — `_DEPRECATED_ALIASES` maps 7 old exception names to new ones
- `rutificador/exceptions.py:128-136` — `__getattr__` shim for deprecated exception aliases
- `rutificador/config.py:54` — `RigorValidacion.LEGADO` member, deprecated since v1.6.0
- `rutificador/validador.py` — protocol `Validador` and class `ValidadorRut` (the `Validador` protocol is deprecated in favor of `ValidadorRut`)
- `ROADMAP.md:49-63` — full table of removals and replacements planned for v2.0
- `pyproject.toml:3` — current version `1.9.0`

Repo conventions:
- All code/docstrings/messages in Spanish
- Conventional Commits: `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`, `release:`
- Version bump must update `pyproject.toml` and `CHANGELOG.md`
- CI enforces `ruff check`, `ruff format`, `mypy`, `deptry`, `lint-imports`

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Tests | `python -m pytest tests/ --ignore=tests/benchmarks --ignore=tests/test_benchmark.py -q -W error::DeprecationWarning` | 268 passed, 0 errors |
| Lint | `python -m ruff check rutificador/` | exit 0 |
| Format | `python -m ruff format --check rutificador/` | exit 0 |
| Types | `python -m mypy rutificador/ --ignore-missing-imports` | exit 0 |
| Dep check | `deptry rutificador` | exit 0 |
| Architecture | `lint-imports` | exit 0 (3 contracts) |
| Migration tool test | `python -m rutificador.migrate --check tests/` | exit 0, scan completes |

## Scope

**In scope** (files you may modify or create):
- `scripts/migrate.py` — NEW: the `rutificador-migrate` CLI script
- `tests/test_migrate.py` — NEW: tests for the migration tool
- `rutificador/__init__.py` — remove deprecated exports and `__getattr__` shim
- `rutificador/exceptions.py` — remove deprecated aliases and `__getattr__` shim
- `rutificador/config.py` — remove `LEGADO` from `RigorValidacion`
- `rutificador/validador.py` — remove `Validador` protocol
- `RU MIGRACION_v2.md` — NEW: comprehensive migration guide
- `ROADMAP.md` — mark v2.0 items as DONE
- `CHANGELOG.md` — add v2.0 entry
- `pyproject.toml` — bump version to `2.0.0`, update Python floor if decided

**Out of scope** (do NOT touch):
- `rutificador/rut.py` — no API changes in this plan
- `rutificador/procesador.py` — no API changes in this plan
- `rutificador/cli.py` — CLI surface unchanged
- `rutificador/contrib/` — integrations unchanged
- Any change to validation logic or DV calculation

## Git workflow

- Branch: `advisor/013-v2-migration-tooling`
- Commit per logical step; message style: Conventional Commits in Spanish
- Example: `feat(migrate): agregar script rutificador-migrate para detección y reemplazo de imports obsoletos`
- Do NOT push or open a PR unless instructed.

## Steps

### Step 1: Crear el script de migración `scripts/migrate.py`

Crear `scripts/migrate.py` con un CLI (argparse) que:

1. **Modo scan** (`--check`): escanea una ruta de directorio o archivo buscando imports de símbolos obsoletos. Lee `_DEPRECATED_EXPORTS` y `_DEPRECATED_ALIASES` para construir el mapa de reemplazos. Emite JSON o texto con: archivo, línea, símbolo obsoleto, reemplazo sugerido. Exit code 0 si no encuentra nada, 1 si encuentra.

2. **Modo fix** (`--fix`): igual que scan, pero reescribe los archivos in-place reemplazando los imports obsoletos por los nuevos. Conserva el resto del archivo intacto.

3. **Modo interactive**: pregunta uno por uno antes de reemplazar.

El script debe:
- Ser standalone (no depende de `rutificador` instalado; el mapa de reemplazos se hardcodea o se lee de una tabla interna)
- Usar `ast.parse` para detectar imports de manera precisa (no regex), modificando solo lo necesario con `ast.unparse`
- Ignorar `tests/`, `.venv/`, `.git/` por defecto
- Soportar `--dry-run` que muestra lo que cambiaría sin escribir

Tabla de reemplazos hardcodeada en el script:

```python
REPLACEMENTS = {
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
```

Estructura de ejemplo:

```python
# scripts/migrate.py
import argparse
import ast
import sys
from pathlib import Path

REPLACEMENTS = {...}

def scan_file(path: Path) -> list[dict]: ...
def fix_file(path: Path, dry_run: bool = False) -> list[dict]: ...
def main(): ...
```

**Verify**: `python scripts/migrate.py --check rutificador/` → exit 0 (ya no debería haber imports obsoletos en el código fuente del propio paquete)

### Step 2: Escribir tests para el script de migración

Crear `tests/test_migrate.py` usando pytest. Casos:

1. **Scan detecta import obsoleto**: crea un archivo temporal con `from rutificador import RutConfig`, ejecuta `--check`, verifica que reporta `RutConfig → ConfiguracionRut`
2. **Scan sale limpio en código moderno**: archivo sin imports obsoletos → exit 0
3. **Fix reemplaza correctamente**: `RutInvalidoError` → `ErrorValidacionRut` en imports y usos
4. **Fix no toca código no relacionado**: verifica que el resto del archivo queda idéntico
5. **--dry-run no escribe cambios**: verifica que el archivo no se modifica
6. **Múltiples reemplazos en un archivo**: varios símbolos obsoletos a la vez

Usar `tmp_path` de pytest para los archivos temporales. Seguir el patrón de `tests/test_cli.py`.

**Verify**: `python -m pytest tests/test_migrate.py -q` → todos pasan

### Step 3: Escribir la guía de migración `GUIA_MIGRACION_v2.md`

Crear `GUIA_MIGRACION_v2.md` en la raíz del repo con:

1. Por qué v2.0 y qué cambia
2. Tabla completa de reemplazos (importada de ROADMAP)
3. Instrucciones para usar `rutificador-migrate`
4. Cómo verificar antes de migrar: `pip install rutificador>=2.0.0 --dry-run`
5. Cómo detectar usos obsoletos con `python -W error::DeprecationWarning`
6. Cambios en `RigorValidacion`: `LEGADO` eliminado, solo `ESTRICTO` y `FLEXIBLE`
7. Cambios en `__init__.py`: sin `__getattr__`
8. FAQ: ¿qué pasa si no migro?, ¿mi código deja de funcionar?

Estructura seguir `CONTRIBUTING.md` como referencia de tono.

### Step 4: Limpiar deprecaciones del código fuente

**IMPORTANTE**: Este paso es el más riesgoso. Procede con cuidado y verifica cada cambio.

#### 4a. `config.py` — eliminar `LEGADO`

En `rutificador/config.py`:
- Eliminar `LEGADO = "legado"` del enum `RigorValidacion`
- Actualizar docstring de la clase para reflejar solo 2 modos
- Verificar que ningún código interno lo referencia: `grep -rn "RigorValidacion.LEGADO\|RigorValidacion\.LEGADO" rutificador/ tests/` debe retornar solo comentarios/docstrings

#### 4b. `exceptions.py` — eliminar aliases obsoletos

En `rutificador/exceptions.py`:
- Eliminar líneas 107-125 (alias a nivel de módulo + `_DEPRECATED_ALIASES`)
- Eliminar `__getattr__` (líneas 128-136)
- Actualizar `__all__` para solo listar los nombres canónicos (líneas 139-154)
- Verificar que ningún código interno importa los nombres viejos: `grep -rn "RutInvalidoError\|RutError\|RutValidationError\|RutFormatError\|RutDigitError\|RutLengthError\|RutProcessingError" rutificador/` debe dar 0 resultados

#### 4c. `__init__.py` — eliminar deprecated exports

En `rutificador/__init__.py`:
- Eliminar `_DEPRECATED_EXPORTS` (líneas 64-68)
- Eliminar `__getattr__` (líneas 71-78)
- Verificar que los imports siguen funcionando: `python -c "from rutificador import ConfiguracionRut, ValidadorRut, ErrorValidacionRut"` debe ejecutar sin error
- Eliminar del `__init__.py` cualquier `import` de `Validador` (el protocolo viejo)

#### 4d. `validador.py` — eliminar protocolo `Validador`

En `rutificador/validador.py`:
- Eliminar la definición del protocolo `Validador` (si existe)
- Verificar que `ValidadorRut` sigue funcionando

**Verify después de todos los sub-pasos**: 
```bash
grep -rn "LEGADO\|RutConfig\|RutValidator\|RutInvalidoError\|RutError\|RutValidationError\|RutFormatError\|RutDigitError\|RutLengthError\|RutProcessingError\|ConsultaRut\|ParametroRut" rutificador/ | grep -v "test_\|\.pyc\|#\|docstring"
```
Debe retornar 0 líneas.

### Step 5: Bump de versión a v2.0.0

En `pyproject.toml`:
- Cambiar `version = "1.9.0"` a `version = "2.0.0"`
- Actualizar `classifiers` si es necesario

En `CHANGELOG.md`:
- Agregar entrada `## [2.0.0] - YYYY-MM-DD`
- Listar todos los breaking changes con tags `[BREAKING]`
- Nota de migración y referencia a `GUIA_MIGRACION_v2.md`

En `ROADMAP.md`:
- Marcar la sección v2.0 como completada
- Actualizar fecha de última actualización

**Verify**: `python -c "import rutificador; print(rutificador.__version__)"` → `2.0.0`

### Step 6: Verificación final completa

Ejecutar todos los gates:

```bash
python -m pytest tests/ --ignore=tests/benchmarks --ignore=tests/test_benchmark.py -q -W error::DeprecationWarning
python -m ruff check rutificador/
python -m ruff format --check rutificador/
python -m mypy rutificador/ --ignore-missing-imports
deptry rutificador
lint-imports
```

**Verify**: todos pasan. Prestar especial atención a que pytest con `-W error::DeprecationWarning` no falle — si falla, es que queda código usando símbolos obsoletos.

## Test plan

- `tests/test_migrate.py` (NUEVO): 6 casos como se describe en Step 2
- Los tests existentes deben seguir pasando sin cambios (los tests internos ya no usan símbolos obsoletos)
- Verificación: `python -m pytest tests/ --ignore=tests/benchmarks --ignore=tests/test_benchmark.py -q` → todos pasan incluyendo los nuevos

## Done criteria

- [ ] `scripts/migrate.py` existe y es ejecutable con `--check`, `--fix`, `--dry-run`
- [ ] `tests/test_migrate.py` con ≥6 tests que pasan
- [ ] `GUIA_MIGRACION_v2.md` completa
- [ ] `grep -rn "LEGADO" rutificador/` retorna 0
- [ ] `grep -rn "__getattr__" rutificador/` retorna 0 (shims eliminados)
- [ ] `grep -rn "RutInvalidoError\|RutConfig\|RutValidator" rutificador/` retorna 0
- [ ] `python -m pytest tests/ --ignore=tests/benchmarks --ignore=tests/test_benchmark.py -q -W error::DeprecationWarning` pasa
- [ ] Todos los gates CI (ruff, mypy, deptry, lint-imports) pasan
- [ ] `pyproject.toml` version es `2.0.0`
- [ ] `plans/README.md` status row updated

## STOP conditions

- Si `grep -rn "RutInvalidoError\|RutError\b\|RutValidationError\|RutFormatError\|RutDigitError\|RutLengthError\|RutProcessingError" tests/` encuentra usos en tests que no son sobre los alias en sí → los tests usan los símbolos viejos y deben migrarse primero
- Si `python -m pytest -W error::DeprecationWarning` falla antes de Step 4 → hay código en tests que usa los símbolos obsoletos; hay que migrar tests también
- Si `import-linter` falla después de remover `Validador` de `__init__.py` → verificar que el protocolo no está en la lista de módulos del contrato
- Si algún test externo (test_property.py, test_spec_vectors.py) falla → revertir y reportar

## Maintenance notes

- Después de este plan, cualquier código que importe `RutConfig` o `RutInvalidoError` fallará con `ImportError` en vez de `DeprecationWarning`. La guía de migración debe ser publicada al menos 6 meses antes del release de v2.0 en PyPI.
- `GUIA_MIGRACION_v2.md` debe mantenerse actualizada si se añaden más deprecaciones entre ahora y el release real de v2.0.
- El script `rutificador-migrate` podría moverse eventualmente a un paquete separado `rutificador-migrate` en PyPI para que sea instalable independientemente.
- Los contrib integraciones (pydantic, fastapi, pandas, polars) no se tocan en este plan; si alguno de ellos usa símbolos obsoletos, eso se aborda en un plan separado.
