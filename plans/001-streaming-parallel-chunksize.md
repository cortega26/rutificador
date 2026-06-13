# Plan 001: Fix the ~10× slowdown of streaming parallel processing

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**:
> `git diff --stat 278425b..HEAD -- rutificador/procesador.py rutificador/cli.py`
> If either in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: perf
- **Planned at**: commit `278425b`, 2026-06-12

## Why this matters

The streaming validation/formatting functions `validar_flujo_ruts` and
`formatear_flujo_ruts` run their parallel path through
`ProcessPoolExecutor.map(...)` **without a `chunksize`**, so the executor
defaults to `chunksize=1` and pickles every single RUT across the process
boundary one at a time. Measured on this machine: 5,000 RUTs take **0.036 s
serial vs 0.368 s with `paralelo=True` — 10.3× slower**. The CLI's
`validar --paralelo` and `formatear --paralelo` route through exactly these
functions, and `README.md:181-182` explicitly tells users to add `--paralelo`
for "heavy files". So the documented way to go faster makes the tool ~10×
slower. Passing a sensible `chunksize` (e.g. 256) restores the expected
speedup: the same 5,000-RUT workload drops to ~0.040 s.

## Current state

- `rutificador/procesador.py` — batch + streaming processing.
  - `validar_flujo_ruts` (lines 337-365): the parallel branch builds a
    generator `cargas` and calls `ejecutor.map(_validar_rut_en_proceso, cargas)`
    with **no `chunksize`** at line ~360.
  - `formatear_flujo_ruts` (lines 368-400): delegates to `validar_flujo_ruts`.
  - The batch method `ProcesadorLotesRut.validar_lista_ruts` (lines 142-189)
    *already* exposes a `chunksize` parameter and computes one with
    `_calcular_chunksize(len(ruts), n_workers)` (line 170). **You must NOT
    reuse that `len()`-based helper here** — the streaming functions accept
    `Iterable[Union[str, int]]` (an unbounded generator), which has no `len()`.
    Calling `len()` on a generator raises `TypeError`. The whole point of the
    streaming API is lazy, unbounded input.
- `rutificador/cli.py` — `_comando_validar` (lines 253-263) and
  `_comando_formatear` (lines 266-278) call `validar_flujo_ruts` /
  `formatear_flujo_ruts` with only `paralelo=args.paralelo`. They rely on the
  default `chunksize`, so giving these functions a good default fixes the CLI
  with no CLI signature change required.

Current parallel branch of `validar_flujo_ruts` (≈ lines 352-361):

```python
    if paralelo:
        configuracion = procesador.validador.configuracion
        modo = procesador.validador.modo
        cargas = ((str(rut), configuracion, modo) for rut in ruts)
        cls_ejecutor = procesador.obtener_clase_ejecutor()

        with cls_ejecutor(max_workers=procesador.max_trabajadores) as ejecutor:
            # yield de los resultados conforme los entrega el ejecutor.map (que ya es perezoso)
            for es_valido, detalle in ejecutor.map(_validar_rut_en_proceso, cargas):
                yield es_valido, detalle
```

**Repo conventions**: Spanish identifiers/comments (neutral Spanish, no
voseo). Module-level constants are UPPER_SNAKE_CASE (see `RUT_REGEX` in
`validador.py`, `_PUNTOS_TRADUCCION` in `utils.py`). Conventional-commit
messages (`fix:`, `perf:`, `chore:` — see `git log`).

## Commands you will need

| Purpose   | Command                                                        | Expected on success |
|-----------|----------------------------------------------------------------|---------------------|
| Setup     | `source .venv/bin/activate` (if a repo-root `.venv` exists) **or** `pip install -r requirements-dev.txt && pip install -e .` | env ready |
| Tests     | `python -m pytest -q tests/test_quick_wins.py tests/test_rutificador.py` | all pass |
| Full suite + deprecations | `python -m pytest -W error::DeprecationWarning -q tests/` | all pass |
| Lint      | `ruff check rutificador/`                                      | `All checks passed!` |
| Format    | `ruff format --check rutificador/`                             | files already formatted |
| Types     | `mypy rutificador/ --ignore-missing-imports`                   | `Success: no issues found` |

## Scope

**In scope** (the only files you should modify):
- `rutificador/procesador.py`
- `tests/test_procesador_flujo.py` (create)

**Out of scope** (do NOT touch):
- `rutificador/cli.py` — no signature change needed; do NOT add a `--chunksize`
  flag (deferred; would broaden the surface and the public CLI contract).
- `ProcesadorLotesRut.validar_lista_ruts` and `_calcular_chunksize` — the batch
  path already chunks correctly; leave it alone.
- The serial branch behavior and the public result types (`RutProcesado`,
  `DetalleError`) — must remain identical.

## Git workflow

- Branch: `advisor/001-streaming-parallel-chunksize`
- One commit; conventional-commit style, e.g.
  `perf: chunk streaming parallel map to fix ~10x slowdown`
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Add a module-level default chunksize constant

Near the top of `rutificador/procesador.py`, after the `logger = ...` line
(around line 44), add:

```python
# Tamaño de lote por defecto para el mapeo paralelo en flujo. Con chunksize=1
# (por defecto de Executor.map) cada RUT se serializa individualmente entre
# procesos, lo que hace el modo paralelo ~10x más lento que el modo serial.
CHUNKSIZE_FLUJO_POR_DEFECTO = 256
```

**Verify**: `python -c "import rutificador.procesador as p; print(p.CHUNKSIZE_FLUJO_POR_DEFECTO)"` → prints `256`

### Step 2: Thread an optional `chunksize` through the two streaming functions

In `validar_flujo_ruts`, add a keyword parameter
`chunksize: int = CHUNKSIZE_FLUJO_POR_DEFECTO` to the signature, and pass it to
the map call. The parallel branch becomes:

```python
        with cls_ejecutor(max_workers=procesador.max_trabajadores) as ejecutor:
            for es_valido, detalle in ejecutor.map(
                _validar_rut_en_proceso, cargas, chunksize=chunksize
            ):
                yield es_valido, detalle
```

In `formatear_flujo_ruts`, add the same
`chunksize: int = CHUNKSIZE_FLUJO_POR_DEFECTO` keyword parameter and forward it
in its call to `validar_flujo_ruts(..., chunksize=chunksize)`.

Do **not** introduce any `len(ruts)` call — `ruts` is an iterable/generator.

**Verify**: `ruff check rutificador/ && mypy rutificador/ --ignore-missing-imports`
→ lint passes, `Success: no issues found`

### Step 3: Write the regression test

Create `tests/test_procesador_flujo.py` (see Test plan below).

**Verify**: `python -m pytest -q tests/test_procesador_flujo.py` → all pass.

## Test plan

Create `tests/test_procesador_flujo.py`. Model the multiprocessing-safety
awareness on `tests/conftest.py` (it already sets the `spawn` start method) and
the property style on `tests/test_property.py`. Cover:

1. **Generator input does not break the parallel path** (this is the core
   guard — a generator has no `len()`, so it catches any reintroduced
   `len(ruts)` call):
   ```python
   from rutificador.procesador import validar_flujo_ruts
   from rutificador.utils import calcular_digito_verificador

   def _muestra(n):
       for i in range(1_000_000, 1_000_000 + n):
           b = str(i)
           yield f"{b}-{calcular_digito_verificador(b)}"

   def test_flujo_paralelo_acepta_generador():
       # Pasar un generador puro (sin __len__) debe funcionar en modo paralelo.
       resultados = list(validar_flujo_ruts(_muestra(50), paralelo=True))
       assert len(resultados) == 50
       assert all(es_valido for es_valido, _ in resultados)
   ```
2. **Parallel results equal serial results** for the same input (order and
   validity preserved):
   ```python
   def test_flujo_paralelo_igual_que_serial():
       datos = list(_muestra(100))
       serial = [(ok, getattr(d, "valor", None)) for ok, d in validar_flujo_ruts(datos, paralelo=False)]
       par = [(ok, getattr(d, "valor", None)) for ok, d in validar_flujo_ruts(datos, paralelo=True)]
       assert serial == par
   ```
3. **`chunksize` is an accepted keyword** and a custom value still yields
   correct results:
   ```python
   def test_flujo_paralelo_chunksize_personalizado():
       datos = list(_muestra(20))
       res = list(validar_flujo_ruts(datos, paralelo=True, chunksize=4))
       assert len(res) == 20 and all(ok for ok, _ in res)
   ```

Verification: `python -m pytest -q tests/test_procesador_flujo.py` → 3 passed.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `python -c "import rutificador.procesador as p; print(p.CHUNKSIZE_FLUJO_POR_DEFECTO)"` prints `256`
- [ ] `grep -n "chunksize=chunksize" rutificador/procesador.py` shows the map call passes it
- [ ] `grep -n "len(ruts)" rutificador/procesador.py` returns **nothing inside `validar_flujo_ruts`/`formatear_flujo_ruts`** (the batch method may still use it — confirm any hit is in `validar_lista_ruts`)
- [ ] `python -m pytest -W error::DeprecationWarning -q tests/` exits 0; the 3 new tests pass
- [ ] `ruff check rutificador/` → `All checks passed!`
- [ ] `ruff format --check rutificador/` → already formatted
- [ ] `mypy rutificador/ --ignore-missing-imports` → `Success`
- [ ] `git status` shows only `rutificador/procesador.py` and `tests/test_procesador_flujo.py` modified/created
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) if:

- The parallel branch of `validar_flujo_ruts` no longer matches the "Current
  state" excerpt (the file drifted).
- Adding `chunksize` to the signature breaks `mypy` because a caller passes it
  positionally — investigate the caller rather than reordering parameters.
- The new generator test hangs (> 15 s) — this can indicate a multiprocessing
  start-method problem; report rather than disabling the test.
- You find a `len()` call is genuinely required for correctness — it is not;
  if you believe it is, the approach is wrong, stop and report.

## Maintenance notes

- Why the fix is safe: `concurrent.futures.Executor.map` eagerly submits all
  tasks from the input iterable before yielding, so `chunksize` changes **only**
  batching, not output ordering — results still arrive in input order, which is
  why `formatear_flujo_ruts` (which relies on order) is unaffected. The
  "no materialization" guarantee of the streaming API was always only true on
  the *output* side; the input side was already consumed eagerly by `map`.
- If a `--chunksize` CLI flag is later added (deferred here), wire it through
  `_comando_validar`/`_comando_formatear` to these same keyword params.
- Reviewer should scrutinize: that no `len()` crept into the streaming path and
  that the default constant is `> 1`.
