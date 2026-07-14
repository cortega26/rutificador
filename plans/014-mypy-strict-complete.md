# Plan 014: Completar rollout de `mypy --strict` en todos los módulos del núcleo

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 6b61e0e..HEAD -- rutificador/rut.py rutificador/procesador.py rutificador/cli.py rutificador/sugestor.py rutificador/exceptions.py rutificador/formatter.py rutificador/contrib/`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P2
- **Effort**: S–M
- **Risk**: LOW
- **Depends on**: none
- **Category**: tech-debt
- **Planned at**: commit `6b61e0e`, 2026-07-14

## Why this matters

Only 5 of 14 source modules have `--strict` mypy enabled (`errores.py`, `version.py`, `config.py`, `utils.py`, `validador.py`). The remaining core modules run under lax mypy which tolerates implicit `Any`, missing return types, and other type-safety gaps. At the time of this plan, running `--strict` on the 6 remaining core modules produces only 6 errors across 2 files — the gap is small and closing it is high-leverage. Strict typing across the entire codebase de-risks v2.0 refactors (plan 013) and any future architecture changes.

## Current state

- **5 modules already `--strict` clean**: `errores.py`, `version.py`, `config.py`, `utils.py`, `validador.py` (CI at `ci.yml:89` verifies this)
- **6 remaining core modules at lax mypy**: `rut.py`, `procesador.py`, `cli.py`, `sugestor.py`, `exceptions.py`, `formatter.py`
- **3 contrib modules at lax mypy**: `contrib/pydantic/`, `contrib/fastapi.py`, `contrib/pandas.py`, `contrib/polars.py`, `contrib/_formato_comun.py`
- Current error count running `--strict` on the 6 core modules: **6 errors** across 2 files:
  - `procesador.py:128` — `obtener_clase_ejecutor` missing return type annotation
  - `procesador.py:173,248,362` — untyped call cascading from above
  - `cli.py:127` — `DictWriter` missing type arguments
  - `cli.py:428` — `main()` returning `Any`

CI command: `python -m mypy --strict rutificador/errores.py rutificador/version.py rutificador/config.py rutificador/utils.py rutificador/validador.py` followed by `python -m mypy rutificador/ --ignore-missing-imports`

Exemplar of already-strict module: `rutificador/config.py` (61 lines, clean `--strict`)

Repo conventions: Python ≥3.10, all public functions and methods have type annotations, Google-style docstrings in Spanish.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Strict check (10 core) | `.venv/bin/python -m mypy --strict rutificador/rut.py rutificador/procesador.py rutificador/cli.py rutificador/sugestor.py rutificador/exceptions.py rutificador/formatter.py rutificador/errores.py rutificador/version.py rutificador/config.py rutificador/utils.py rutificador/validador.py` | exit 0, no errors |
| Full project check | `.venv/bin/python -m mypy rutificador/ --ignore-missing-imports` | exit 0, no errors |
| Tests | `.venv/bin/python -m pytest tests/ --ignore=tests/benchmarks --ignore=tests/test_benchmark.py -q` | 268 passed |
| Lint | `.venv/bin/python -m ruff check rutificador/` | exit 0 |

## Scope

**In scope** (fix `--strict` errors in):
- `rutificador/procesador.py` — add return type to `obtener_clase_ejecutor`
- `rutificador/cli.py` — add type args to `DictWriter`, add return type annotation

**Out of scope** (do NOT touch):
- `rutificador/contrib/` — optional dependencies; `--strict` on these is deferred to a follow-up because `pandas`, `polars`, `fastapi`, `pydantic` stubs may be incomplete
- Any functional logic changes — only type annotations
- Tests — no test changes needed unless they import from the changed symbols

## Git workflow

- Branch: `advisor/014-mypy-strict-complete`
- Commit per file fixed; message style: `refactor(types): habilitar mypy --strict en <module>.py`
- Example: `refactor(types): habilitar mypy --strict en procesador.py`
- Do NOT push or open a PR unless instructed.

## Steps

### Step 1: Fix `procesador.py` — add return type to `obtener_clase_ejecutor`

In `rutificador/procesador.py:128`, the method `obtener_clase_ejecutor` is missing a return type annotation. The method returns either `ProcessPoolExecutor` or `ThreadPoolExecutor` — both are subclasses of `concurrent.futures.Executor`.

Change line 128 from:
```python
    def obtener_clase_ejecutor(self):
```
To:
```python
    def obtener_clase_ejecutor(self) -> type[ThreadPoolExecutor | ProcessPoolExecutor]:
```

Or, if you prefer to use the base class:
```python
from concurrent.futures import Executor
    def obtener_clase_ejecutor(self) -> type[Executor]:
```

Use the second option (`type[Executor]`) — it's simpler and more correct (the return value is a class, not an instance).

The import `ThreadPoolExecutor, ProcessPoolExecutor` is already at line 16. Add `Executor` to that import:
```python
from concurrent.futures import Executor, ProcessPoolExecutor, ThreadPoolExecutor
```

**Verify**: `.venv/bin/python -m mypy --strict rutificador/procesador.py` → exit 0

### Step 2: Fix `cli.py` — type arguments for `DictWriter`

In `rutificador/cli.py:127`, the `self._escritor` attribute is typed as `Optional[csv.DictWriter]` without type arguments. `DictWriter` is generic in `DictWriter[Any]`.

Change line 127 from:
```python
        self._escritor: Optional[csv.DictWriter] = None
```
To:
```python
        self._escritor: Optional[csv.DictWriter[Any]] = None
```

The `Any` import is already available at line 16: `from typing import Any, Dict, Iterator, List, Literal, Optional, Union`.

**Verify**: `.venv/bin/python -m mypy --strict rutificador/cli.py` → exit 0

### Step 3: Fix `cli.py` — ensure `main()` returns `int`, not `Any`

In `rutificador/cli.py:428`, `main()` calls `args.func(args)` which argparse populates via `set_defaults(func=_comando_validar)`. Since `func` is set dynamically, mypy can't infer the return type.

Change line 428 from:
```python
    return args.func(args)
```
To:
```python
    result = args.func(args)
    return int(result)
```

(`args.func` returns `int` from all command handlers, as seen in `_comando_validar`, `_comando_formatear`, `_comando_enmascarar`, `_comando_info` — they all return `int`. The cast ensures mypy is satisfied without changing any runtime behavior.)

**Verify**: `.venv/bin/python -m mypy --strict rutificador/cli.py` → exit 0

### Step 4: Verify remaining 4 modules pass `--strict` with no changes needed

```bash
.venv/bin/python -m mypy --strict rutificador/rut.py rutificador/sugestor.py rutificador/exceptions.py rutificador/formatter.py
```

Expected: exit 0, no errors (these already pass — confirmed during recon).

### Step 5: Enable all 10 core modules in CI

In `.github/workflows/ci.yml:89`, expand the `--strict` line to cover all 10 core modules:

Change line 89 from:
```yaml
        python -m mypy --strict rutificador/errores.py rutificador/version.py rutificador/config.py rutificador/utils.py rutificador/validador.py
```
To:
```yaml
        python -m mypy --strict rutificador/errores.py rutificador/version.py rutificador/config.py rutificador/utils.py rutificador/validador.py rutificador/rut.py rutificador/procesador.py rutificador/cli.py rutificador/sugestor.py rutificador/exceptions.py rutificador/formatter.py
```

### Step 6: Full verification

```bash
# All 10 core modules strict-clean
.venv/bin/python -m mypy --strict rutificador/errores.py rutificador/version.py rutificador/config.py rutificador/utils.py rutificador/validador.py rutificador/rut.py rutificador/procesador.py rutificador/cli.py rutificador/sugestor.py rutificador/exceptions.py rutificador/formatter.py

# Full project still clean
.venv/bin/python -m mypy rutificador/ --ignore-missing-imports

# No regressions
.venv/bin/python -m pytest tests/ --ignore=tests/benchmarks --ignore=tests/test_benchmark.py -q
.venv/bin/python -m ruff check rutificador/
.venv/bin/python -m ruff format --check rutificador/
```

**Verify**: all commands exit 0.

## Test plan

No new tests needed — this is a type-level change only. The existing test suite (`268 passed`) serves as the regression gate. If any test fails after the changes, the type annotation was incorrect — review the change.

## Done criteria

- [ ] `mypy --strict` passes on all 10 core modules
- [ ] `mypy rutificador/ --ignore-missing-imports` passes
- [ ] CI workflow updated to enforce `--strict` on all 10 core modules
- [ ] `pytest` passes (268 tests, no regressions)
- [ ] `ruff check` and `ruff format --check` pass
- [ ] No functional code changes beyond type annotations
- [ ] `plans/README.md` status row updated

## STOP conditions

- If adding `type[Executor]` as the return type of `obtener_clase_ejecutor` causes mypy to reject the callsites (lines 173, 248, 362), use `type[ThreadPoolExecutor | ProcessPoolExecutor]` instead and import `ThreadPoolExecutor` and `ProcessPoolExecutor` from `concurrent.futures` (already importing them at line 16)
- If `int(result)` in `main()` causes mypy to complain about the cast, wrap it as `result: int = args.func(args)  # type: ignore[no-any-return]` instead. Re-run tests to confirm no regression
- If any of the 4 "already clean" modules (rut.py, sugestor.py, exceptions.py, formatter.py) produces errors under `--strict`, stop and report — the codebase has drifted

## Maintenance notes

- `rutificador/contrib/` modules are explicitly excluded from `--strict` in this plan because they depend on optional third-party packages whose stubs may be incomplete. A future plan could tackle them individually.
- If a new core module is added to `rutificador/`, it should be added to the `--strict` list in CI from day one.
- The pattern established in `ci.yml:89` is to have a separate `--strict` line (explicit file list) followed by a project-wide lax check. Keep this pattern.
