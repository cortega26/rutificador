# Plan 002: Pin current behavior with characterization tests (constructor↔parse, parallel paths)

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**:
> `git diff --stat 278425b..HEAD -- rutificador/rut.py rutificador/procesador.py`
> If either file changed since this plan was written, the *documented current
> behavior* below may be stale — re-derive the expected values empirically
> (Step 1) before asserting them.

## Status

- **Priority**: P1
- **Effort**: S–M
- **Risk**: LOW
- **Depends on**: none (but is a prerequisite for plan 003)
- **Category**: tests
- **Planned at**: commit `278425b`, 2026-06-12

## Why this matters

`Rut(s)` (the constructor) and `Rut.parse(s)` are two independent
implementations of the same RUT grammar. They currently **disagree** on some
inputs (plan 003 addresses the disagreement). Before anyone changes either
path, we need tests that pin today's behavior so the change in 003 is a
*deliberate, visible* diff and not a silent regression. There is currently **no
test** asserting any relationship between the two entry points, and the
process-parallel branches of `procesador.py` (lines ~353-361) are uncovered.
This plan adds characterization tests only — it does **not** change any
behavior.

## Current state

- `rutificador/rut.py`:
  - Constructor `Rut.__init__` (lines 415-442) → `_analizar_y_validar`
    (444-458): calls `_limpiar_entrada(str(rut).strip())` **unconditionally**
    (line 436), which strips internal whitespace, then validates via
    `ValidadorRut.validar_formato`.
  - `Rut.parse` (lines 263-334): uses `Rut.normalizar` (211-261), whose
    `_verificar_espacios` (100-114) **rejects** internal whitespace in
    `ESTRICTO` mode.
  - Observed today (verify in Step 1, do not trust blindly):
    - `Rut("12345678-5")` → valid; `Rut.parse("12345678-5").estado == "valido"`. **Agree.**
    - `Rut("12345678")` (no DV) → **succeeds** (constructor computes DV);
      `Rut.parse("12345678").estado` → `"posible"` (not `"valido"`). **Differ, by design.**
    - `Rut("12 345678-5")` (internal space) → **succeeds** (space stripped);
      `Rut.parse("12 345678-5").estado` → `"invalido"`. **Differ — this is the
      strictness gap plan 003 will resolve.**
- `rutificador/procesador.py`: `validar_flujo_ruts(..., paralelo=True)` and
  `ProcesadorLotesRut.validar_lista_ruts(..., paralelo=True)` exercise the
  multiprocessing branch.

**Repo conventions**: pytest, tests in `tests/`, Spanish names. Property-based
tests use Hypothesis (`tests/test_property.py`). Multiprocessing tests rely on
`tests/conftest.py` which sets the `spawn` start method. CLI/subprocess tests
in `tests/test_cli.py`.

## Commands you will need

| Purpose   | Command                                                        | Expected on success |
|-----------|----------------------------------------------------------------|---------------------|
| Setup     | `source .venv/bin/activate` (if present) **or** `pip install -r requirements-dev.txt && pip install -e .` | env ready |
| Run new tests | `python -m pytest -q tests/test_consistencia_parse.py tests/test_procesador_paralelo.py` | all pass |
| Full suite | `python -m pytest -W error::DeprecationWarning -q tests/`     | all pass |
| Lint/format | `ruff check tests/ && ruff format --check tests/`            | passes |

## Scope

**In scope** (create only):
- `tests/test_consistencia_parse.py` (create)
- `tests/test_procesador_paralelo.py` (create)

**Out of scope** (do NOT modify):
- Any file under `rutificador/` — this plan adds tests only, changes no
  behavior. If a test you write fails against current code, that means your
  *expected value is wrong*, not the code — re-derive it empirically (Step 1).
- `tests/test_procesador_flujo.py` — that file belongs to plan 001.

## Git workflow

- Branch: `advisor/002-characterization-tests`
- One commit: `test: characterize constructor/parse behavior and parallel paths`
- Do NOT push or open a PR unless instructed.

## Steps

### Step 1: Empirically derive today's behavior (do not skip)

Run this and record the actual output — these are the values your tests assert:

```bash
python - <<'PY'
import logging; logging.disable(logging.CRITICAL)
from rutificador.rut import Rut
casos = ["12345678-5", "12345678", "12 345678-5", "1", "0", "12.345.678-5",
         "12345678-K", "  ", "999999999-9"]
def ctor(s):
    try: Rut(s); return "ok"
    except Exception as e: return type(e).__name__
for s in casos:
    print(repr(s), "| ctor=", ctor(s), "| parse=", Rut.parse(s).estado)
PY
```

**Verify**: command prints one line per case. Use these exact `estado` values
and ctor outcomes in Step 2 — do not guess.

### Step 2: Write the constructor↔parse characterization test

Create `tests/test_consistencia_parse.py`. For each case from Step 1, assert
both the constructor outcome (valid / raises) and `Rut.parse(s).estado`. Add a
table-driven test plus an explicit **documented-divergence** test that pins the
whitespace gap so plan 003's change is visible:

```python
import logging
import pytest
from rutificador.rut import Rut

logging.disable(logging.CRITICAL)

def _ctor_valido(s: str) -> bool:
    try:
        Rut(s)
        return True
    except Exception:
        return False

# (entrada, ctor_valido_esperado, parse_estado_esperado) — valores derivados
# empíricamente del comportamiento ACTUAL (commit 278425b). No son un ideal;
# documentan lo que hoy ocurre para detectar cambios deliberados.
CASOS = [
    ("12345678-5", True, "valido"),
    ("12.345.678-5", True, "valido"),
    # ... completar desde la salida del Paso 1 ...
]

@pytest.mark.parametrize("entrada, ctor_ok, estado", CASOS)
def test_comportamiento_actual_ctor_y_parse(entrada, ctor_ok, estado):
    assert _ctor_valido(entrada) is ctor_ok
    assert Rut.parse(entrada).estado == estado

def test_divergencia_espacios_documentada():
    """Hoy el constructor acepta espacios internos y parse (ESTRICTO) los rechaza.
    Plan 003 resolverá esta inconsistencia; este test la fija para hacer
    visible ese cambio."""
    entrada = "12 345678-5"
    assert _ctor_valido(entrada) is True          # constructor limpia espacios
    assert Rut.parse(entrada).estado == "invalido" # parse ESTRICTO los rechaza
```

**Verify**: `python -m pytest -q tests/test_consistencia_parse.py` → all pass.

### Step 3: Write the parallel-path coverage test

Create `tests/test_procesador_paralelo.py` exercising the multiprocessing
branch of both the batch and streaming APIs, asserting parity with serial:

```python
from rutificador.procesador import validar_lista_ruts, ProcesadorLotesRut
from rutificador.utils import calcular_digito_verificador

def _datos(n=60):
    out = []
    for i in range(1_000_000, 1_000_000 + n):
        b = str(i)
        out.append(f"{b}-{calcular_digito_verificador(b)}")
    return out

def test_validar_lista_paralelo_igual_que_serial():
    datos = _datos()
    p = ProcesadorLotesRut()
    serial = p.validar_lista_ruts(datos, paralelo=False)
    par = p.validar_lista_ruts(datos, paralelo=True)
    assert serial.ruts_validos == par.ruts_validos
    assert len(serial.ruts_invalidos) == len(par.ruts_invalidos)

def test_funcion_modulo_validar_lista_paralelo():
    datos = _datos()
    res = validar_lista_ruts(datos, paralelo=True)
    assert len(res["validos"]) == len(datos)
```

**Verify**: `python -m pytest -q tests/test_procesador_paralelo.py` → all pass.

## Test plan

- New files: `tests/test_consistencia_parse.py` (Step 2),
  `tests/test_procesador_paralelo.py` (Step 3).
- Pattern sources: `tests/test_property.py` (style), `tests/conftest.py`
  (spawn start method already handles process safety — no extra setup needed).
- Verification: `python -m pytest -W error::DeprecationWarning -q tests/`
  → all pass, including the new tests; total test count increases.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `python -m pytest -W error::DeprecationWarning -q tests/` exits 0
- [ ] `tests/test_consistencia_parse.py` exists and contains
      `test_divergencia_espacios_documentada`
- [ ] `tests/test_procesador_paralelo.py` exists and its tests pass
- [ ] `git status` shows only the two new test files added; **no file under
      `rutificador/` is modified**
- [ ] `ruff check tests/` passes
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back if:

- A characterization assertion you derived in Step 1 fails when run in Step 2 —
  this means the file drifted from this plan; report the actual Step 1 output.
- The parallel test hangs (> 15 s) — likely a multiprocessing start-method
  issue; report, do not delete the test.
- You feel the urge to "fix" the whitespace divergence here — that is plan 003.
  This plan must not change any `rutificador/` code.

## Maintenance notes

- These tests intentionally encode *current* behavior, including the
  whitespace divergence, which is a known gap. When plan 003 lands,
  `test_divergencia_espacios_documentada` is expected to be **updated** (the
  whole point), and that update is the visible proof of the behavior change.
- Reviewer should confirm the asserted values came from Step 1's real output,
  not from assumptions.
