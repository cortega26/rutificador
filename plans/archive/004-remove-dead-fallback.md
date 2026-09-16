# Plan 004: Remove the unreachable fallback branch in `formatear_lista_ruts`

> **Executor instructions**: Follow step by step, run every verification
> command, honor STOP conditions, update this plan's row in `plans/README.md`
> when done (unless a reviewer owns the index).
>
> **Drift check (run first)**:
> `git diff --stat 278425b..HEAD -- rutificador/procesador.py`
> If the file changed, re-verify the "Current state" excerpt before editing; on
> mismatch, STOP.

## Status

- **Priority**: P3
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: tech-debt
- **Planned at**: commit `278425b`, 2026-06-12

## Why this matters

`ProcesadorLotesRut.formatear_lista_ruts` has a fallback branch that
reconstructs `RutProcesado` objects from `ruts_validos` when `detalles_validos`
is empty. But `validar_lista_ruts` appends to `ruts_validos` and
`detalles_validos` **together** in the same loop iteration (lines 182-183), so
the two lists always have equal length: `detalles_validos` is empty **iff**
`ruts_validos` is empty. Therefore the fallback's list comprehension always
produces `[]` in exactly the case it triggers — it is dead code. It also
carries a latent bug (`cadena.split("-")[0]`/`[-1]` would misbehave on
DV-less strings), so removing it eliminates both noise and a trap.

## Current state

`rutificador/procesador.py`, inside `formatear_lista_ruts` (lines ~233-245):

```python
        resultado_validacion = self.validar_lista_ruts(ruts, paralelo=paralelo)
        partes: List[str] = ["RUTs válidos:"]
        fuentes = resultado_validacion.detalles_validos

        if not fuentes:
            fuentes = [
                RutProcesado(
                    valor=cadena,
                    base=cadena.split("-")[0],
                    digito=cadena.split("-")[-1],
                    validador_modo=self.validador.modo.value,
                )
                for cadena in resultado_validacion.ruts_validos
            ]
```

Producer that guarantees the invariant — `validar_lista_ruts` (lines 179-186):

```python
        for es_valido, valor in resultados:
            if es_valido:
                detalle = valor  # RutProcesado
                resultado.ruts_validos.append(detalle.valor)
                resultado.detalles_validos.append(detalle)
            else:
                resultado.ruts_invalidos.append(valor)
```

**Repo conventions**: Spanish identifiers/comments; conventional commits.

## Commands you will need

| Purpose   | Command                                                        | Expected |
|-----------|----------------------------------------------------------------|----------|
| Setup     | `source .venv/bin/activate` (if present) **or** `pip install -r requirements-dev.txt && pip install -e .` | env ready |
| Targeted tests | `python -m pytest -q tests/test_rutificador.py tests/test_additional.py` | all pass |
| Full suite | `python -m pytest -W error::DeprecationWarning -q tests/`     | all pass |
| Coverage check | `python -m pytest -q --cov=rutificador.procesador --cov-report=term-missing tests/` | see Step 2 |
| Lint/types | `ruff check rutificador/ && mypy rutificador/ --ignore-missing-imports` | pass |

## Scope

**In scope**:
- `rutificador/procesador.py` — remove the dead `if not fuentes:` block only.

**Out of scope**:
- `validar_lista_ruts` and the invariant itself — do not change how
  `ruts_validos`/`detalles_validos` are populated.
- The empty-input behavior of `formatear_lista_ruts` (it already handles an
  empty `fuentes` by producing an empty formatted section) — must be preserved.

## Git workflow

- Branch: `advisor/004-remove-dead-fallback`
- Commit: `refactor: drop unreachable fallback in formatear_lista_ruts`
- Do NOT push/PR unless instructed.

## Steps

### Step 1: Confirm the branch is unreachable, then delete it

First prove it empirically (the fallback must be a no-op even when it runs):

```bash
python - <<'PY'
from rutificador.procesador import ProcesadorLotesRut
# Empty input: detalles_validos empty -> fallback would run -> must yield empty.
out = ProcesadorLotesRut().formatear_lista_ruts([])
print("OK empty:", "RUTs válidos:" in out)
# All-invalid input: ruts_validos empty too -> fallback yields [].
out2 = ProcesadorLotesRut().formatear_lista_ruts(["not-a-rut"])
print("OK invalid:", "RUTs inválidos:" in out2)
PY
```

Then edit `formatear_lista_ruts` so the block becomes simply:

```python
        resultado_validacion = self.validar_lista_ruts(ruts, paralelo=paralelo)
        partes: List[str] = ["RUTs válidos:"]
        fuentes = resultado_validacion.detalles_validos
```

(Delete the entire `if not fuentes:` block. Do not remove the `RutProcesado`
import — confirm it is still used elsewhere in the file first with
`grep -n "RutProcesado" rutificador/procesador.py`; it is used in type hints
and `_validar_rut_local`, so keep the import.)

**Verify**: `python -m pytest -W error::DeprecationWarning -q tests/` → all
pass (no test should depend on the removed branch).

### Step 2: Confirm no coverage/behavior regression

**Verify**:
- `grep -n "if not fuentes" rutificador/procesador.py` → no matches.
- `python -m pytest -q --cov=rutificador.procesador --cov-report=term-missing tests/`
  → `formatear_lista_ruts` still covered; total suite still green.

## Test plan

No new test required — existing tests in `tests/test_rutificador.py` /
`tests/test_additional.py` already exercise `formatear_lista_ruts` with valid,
invalid, mixed, and empty inputs. If `grep -rn "formatear_lista_ruts" tests/`
shows **no** empty-input case, add one small test asserting
`"RUTs válidos:" in formatear_lista_ruts([])` to lock the preserved behavior.

Verification: `python -m pytest -W error::DeprecationWarning -q tests/` → all pass.

## Done criteria

- [ ] `grep -n "if not fuentes" rutificador/procesador.py` returns nothing
- [ ] `python -m pytest -W error::DeprecationWarning -q tests/` exits 0
- [ ] `ruff check rutificador/` passes; `mypy rutificador/ --ignore-missing-imports` → `Success`
- [ ] `git status` shows only `rutificador/procesador.py` (and optionally one
      test file) modified
- [ ] `plans/README.md` status row updated

## STOP conditions

- Removing the block makes any existing test fail — that would mean the branch
  was *not* dead; STOP and report which test and input reached it.
- The "Current state" excerpt does not match live code (drift).

## Maintenance notes

- The invariant that makes this safe is "`ruts_validos` and `detalles_validos`
  are populated in lockstep by `validar_lista_ruts`". If a future change ever
  populates `ruts_validos` without a corresponding `RutProcesado`, this fallback
  would have been needed — but the correct fix then is to preserve the
  invariant, not to resurrect string-splitting.
