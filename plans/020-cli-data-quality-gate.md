# Plan 020: CLI `validar` como gate de calidad — flag `--max-tasa-error`

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat d6c28d8..HEAD -- rutificador/cli.py tests/test_cli.py docs/guia/cli.md README.md CHANGELOG.md pyproject.toml`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW (flag opt-in; comportamiento sin flag intacto)
- **Depends on**: none
- **Category**: direction
- **Planned at**: commit `d6c28d8`, 2026-09-15

## Why this matters

La CLI ya emite resultados estructurados y códigos de salida, y hoy
`validar` retorna `1` si *cualquier* fila es inválida. En pipelines ETL
reales un pequeño porcentaje de filas sucias es esperado, así que el gate
actual (tolerancia cero) no sirve como control de calidad en CI: o es
demasiado estricto o los equipos lo ignoran. Un flag
`--max-tasa-error <0..1>` convierte `validar` en un gate utilizable
(falla solo si la tasa de inválidos supera el umbral), sin cambiar nada
para quien no lo usa.

## Current state

- `rutificador/cli.py:175-242` — `_emitir_resultados(resultados, formato,
  usar_sugerencias=False, quiet=False) -> int`. Cuenta `total`/`validos`;
  pone `codigo_salida = 1` si hay algún inválido (`cli.py:211`); construye
  `metadata = {"audit": {"version", "total", "validos", "invalidos",
  "tiempo_segundos", "tasa_exito"}}` (`cli.py:228-237`); retorna el código.
- `rutificador/cli.py:255-265` — `_comando_validar(args)` delega en
  `_emitir_resultados` y retorna su código. No hay noción de umbral.
- `rutificador/cli.py:337-358` — el parser crea `validar` y `formatear`
  con args comunes (`archivo`, `--format`, `--paralelo`, `--mejorar`,
  `--sugerir`, `--quiet`); `validar` usa `_comando_validar` (`cli.py:358`).
- `rutificador/cli.py:426-430` — `main(argv) -> int` retorna el código del
  subcomando; `__main__` hace `sys.exit(main())`.
- Patrón de tests CLI en `tests/test_cli.py:13-35`: helper `ejecutar_cli`
  (subprocess `python -m rutificador.cli`, `check=False`, `timeout=15`) y
  asserts sobre `stdout`/`stderr`/`returncode`; también invocación directa
  `cli.main([...])` con `tmp_path` (`test_cli.py:46-56`).
- Docs CLI en `docs/guia/cli.md` (nav `mkdocs.yml`) y sección CLI del
  `README.md`. `CHANGELOG.md` sigue Keep a Changelog.
- Gate de versionado (`.github/workflows/version-bump-gate.yml`): cualquier
  cambio en `rutificador/` exige bump en `rutificador/version.py`, que lee
  la versión de `[tool.poetry] version` en `pyproject.toml` (hoy `2.0.0`).
  Este plan toca `rutificador/cli.py`, así que el bump es obligatorio:
  `2.0.0 → 2.1.0` (flag nuevo retrocompatible = MINOR por SemVer y por la
  política en `ROADMAP.md:75-81`).

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---------|---------|------------|---------------------|
| Baseline tests | `.venv/bin/python -m pytest tests/ --ignore=tests/benchmarks --ignore=tests/test_benchmark.py -q` | declared | all pass |
| Lint | `.venv/bin/ruff check .` | declared | All checks passed |
| Format | `.venv/bin/ruff format --check .` | declared | already formatted |
| Types | `.venv/bin/mypy rutificador/ --ignore-missing-imports` | declared | no issues |
| CLI manual | `.venv/bin/python -m rutificador.cli validar --help` | declared | muestra `--max-tasa-error` |

## Scope

**In scope**:

- `rutificador/cli.py` (flag, cómputo de tasa, exit code 2)
- `tests/test_cli.py` (nuevos tests del flag)
- `docs/guia/cli.md` (documentar flag + exit codes)
- `README.md` (solo la sección CLI, una viñeta + ejemplo)
- `CHANGELOG.md` (entrada `[2.1.0]` con el flag)
- `pyproject.toml` (solo `version = "2.0.0"` → `"2.1.0"`)

**Out of scope** (NO tocar):

- `formatear`, `enmascarar`, `info` — el gate aplica solo a `validar`
  (en formatear "inválido" tiene otra semántica; ver diferidos).
- `rutificador/version.py` — lee la versión dinámicamente, no se edita.
- `tests/vectors/*`, schemas de salidas (plan 021 los cubrirá después;
  este plan debe aterrizar primero para que las formas sean finales).
- Cambios al formato de `metadata["audit"]` salvo agregar el campo de tasa
  documentado abajo (el plan 021 hará snapshot de lo que quede).

## Git workflow

- Branch: `advisor/020-cli-data-quality-gate`
- Commit por unidad lógica; estilo conventional commits como en `git log`
  (ej.: `feat(cli): agregar --max-tasa-error a validar`).
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 0: Establish a green baseline

Corre la tabla de comandos sobre el checkout sin modificar. Todo debe
pasar antes de tocar código.

**Verify**: tests en verde; `ruff check` y `mypy` limpios.

### Step 1: Agregar `--max-tasa-error` al parser de `validar`

En `_crear_parser` (`cli.py:337-358`), dentro del `if sub == "validar"`
(`cli.py:357-358`), agrega:

```python
p.add_argument(
    "--max-tasa-error",
    type=float,
    default=None,
    help="Tasa máxima tolerada de RUTs inválidos (0.0-1.0). "
    "Si se supera, validar retorna exit code 2.",
)
```

Valida el rango en `_comando_validar`: si el valor no es `None` y está
fuera de `[0.0, 1.0]`, imprime error a `stderr` y retorna `2`
(`argparse` `type=float` ya rechaza no-numéricos con exit 2 propio; no
dupliques eso).

**Verify**: `.venv/bin/python -m rutificador.cli validar --help` muestra
el flag; `--max-tasa-error 9` retorna `2`; `--max-tasa-error abc`
lo rechaza argparse (exit 2).

### Step 2: Aplicar el umbral en `_emitir_resultados`

Firma nueva (parámetro optativo al final para no romper llamadas):

```python
def _emitir_resultados(
    resultados, formato, usar_sugerencias=False, quiet=False,
    max_tasa_error: float | None = None,
) -> int:
```

Lógica (después del loop, donde ya existen `total`/`validos`):

- `tasa_error = (total - validos) / total if total > 0 else 0.0`.
- Agrega `"tasa_error": round(tasa_error, 4)` al dict `audit` de
  `metadata` (junto a `tasa_exito`; no renombres ni quites claves).
- Si `max_tasa_error is not None and tasa_error > max_tasa_error`:
  imprime a `stderr` un mensaje `Tasa de error {tasa:.1%} supera el máximo
  tolerado {max:.1%} ({invalidos}/{total})` y retorna `2`.
- Sin flag: comportamiento idéntico al actual (`0` todo válido, `1` si
  hay algún inválido).

Pasa `max_tasa_error=args.max_tasa_error` en `_comando_validar`.
`_comando_formatear` no lo pasa (queda en default `None`).

**Verify**: con stdin `12345678-5\n12345678-9\n`
(tasa 50 %): sin flag → exit `1` (igual que antes);
`--max-tasa-error 0.6` → exit `1`; `--max-tasa-error 0.4` → exit `2` y
mensaje en `stderr`; todo-válido + `--max-tasa-error 0.0` → exit `0`.

### Step 3: Tests en `tests/test_cli.py`

Sigue el patrón `ejecutar_cli` + asserts de `returncode`/`stderr`
(`test_cli.py:13-35`):

1. `test_validar_max_tasa_error_tolera`: 1 válido + 1 inválido con
   `--max-tasa-error 0.5` → exit `0`.
2. `test_validar_max_tasa_error_excede`: mismo input con
   `--max-tasa-error 0.49` → exit `2` y `supera el máximo` en `stderr`.
3. `test_validar_max_tasa_error_fuera_de_rango`: `--max-tasa-error 1.5`
   → exit `2`.
4. `test_validar_sin_flag_compatible`: 1 válido + 1 inválido sin flag →
   exit `1` (regresión del comportamiento previo).
5. `test_metadata_incluye_tasa_error`: `validar --format json` sobre
   input mixto → parsear `stdout` como JSON y assert
   `"tasa_error" in <metadata audit>` con valor `0.5`.

**Verify**: `.venv/bin/python -m pytest tests/test_cli.py -q` → all pass
(incluye los 5 nuevos).

### Step 4: Docs, changelog y versión

1. `docs/guia/cli.md`: documenta el flag, la tabla de exit codes
   (`0` todo válido / bajo umbral, `1` inválidos sin flag o bajo... —
   escribe la tabla exacta: `0` = ok; `1` = hay inválidos (sin flag o
   tasa dentro del umbral); `2` = umbral superado o uso inválido) y un
   ejemplo de uso en CI (`rutificador validar ruts.txt --max-tasa-error
   0.01 --quiet || echo "gate fallido"`).
2. `README.md`: solo la sección CLI — una viñeta + el ejemplo corto.
3. `CHANGELOG.md`: nueva sección `## [2.1.0]` (fecha del día) con
   `- [FEAT] CLI validar: flag --max-tasa-error ...`.
4. `pyproject.toml`: `version = "2.0.0"` → `"2.1.0"` (una línea, nada más).

**Verify**: `grep -n "max-tasa-error" docs/guia/cli.md README.md
CHANGELOG.md` retorna matches; `grep -n '^version' pyproject.toml`
muestra `2.1.0`.

### Step 5: Puerta de calidad completa

Corre tabla completa: tests (con ignores), `ruff check .`,
`ruff format --check .`, `mypy rutificador/ --ignore-missing-imports`.

**Verify**: todo verde; `git diff --name-only d6c28d8...HEAD` lista solo
archivos del Scope.

## Test plan

Ver paso 3 (5 tests nuevos en `tests/test_cli.py`, patrón `ejecutar_cli`
de `test_cli.py:13-35`). Casos: tolera, excede (exit 2 + stderr),
fuera-de-rango, compatibilidad sin flag, `tasa_error` en metadata JSON.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `.venv/bin/python -m pytest tests/ --ignore=tests/benchmarks --ignore=tests/test_benchmark.py -q` → all pass
- [ ] `.venv/bin/ruff check .` → All checks passed; `ruff format --check .` OK
- [ ] `.venv/bin/mypy rutificador/ --ignore-missing-imports` → no issues
- [ ] `validar` sin flag sobre input mixto retorna `1`; con
  `--max-tasa-error` bajo la tasa retorna `1` o `0` según corresponda y
  sobre ella retorna `2`
- [ ] `git diff --name-only d6c28d8...HEAD` lista solo archivos del Scope
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) if:

- El código de `cli.py` no coincide con los extractos (drift).
- `_emitir_resultados` ya no retorna `1` ante inválidos o su firma cambió
  de forma incompatible con lo descrito.
- `docs/guia/cli.md` no existe o el `README.md` no tiene sección CLI
  donde documentar (no crees páginas nuevas en este plan).
- El gate de versionado exige algo distinto a bump de `pyproject.toml`
  (lee `.github/workflows/version-bump-gate.yml` si el mensaje de CI
  difiere).
- Una verificación falla dos veces tras un intento razonable.

## Maintenance notes

- El plan 021 (schemas) hará snapshot de `metadata["audit"]` y de los
  exit codes: debe ejecutarse DESPUÉS de este plan o sus schemas nacerán
  desactualizados (registrado en `plans/README.md` como dependencia).
- Revisores: el exit `2` colisiona a propósito con el `2` de argparse
  ante uso inválido; ambos significan "invocación/entorno no aceptable"
  y están documentados juntos en la tabla.
- **Deferred:** `--max-tasa-error` en `formatear` — semántica distinta
  (filas inválidas no se formatean); requiere decisión de producto, no es
  parte de este plan. **Deferred:** gate por conteo absoluto
  (`--max-errores N`) — se descartó por redundante con la tasa; reabrir
  solo con demanda.
