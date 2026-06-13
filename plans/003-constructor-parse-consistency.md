# Plan 003: Resolve the constructor↔parse whitespace strictness inconsistency

> **Executor instructions**: This plan has a **DECISION GATE** in Step 1. Do
> not write code until the gate is resolved. Follow the steps, run every
> verification command, honor the STOP conditions, and update this plan's row
> in `plans/README.md` when done (unless a reviewer told you they own the
> index).
>
> **Drift check (run first)**:
> `git diff --stat 278425b..HEAD -- rutificador/rut.py rutificador/validador.py rutificador/utils.py`
> If any in-scope file changed, re-verify the "Current state" excerpts against
> live code before proceeding; on mismatch, STOP.

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: MED
- **Depends on**: plans/002-characterization-tests.md (must be DONE first)
- **Category**: correctness / consistency
- **Planned at**: commit `278425b`, 2026-06-12

## Why this matters

`Rut(s)` and `Rut.parse(s)` are documented as two views of the same validation
(CLAUDE.md calls `parse()` "the exception-safe alternative" to the
constructor), yet in `ESTRICTO` mode they **disagree on whitespace**: the
constructor unconditionally strips internal spaces and accepts
`Rut("12 345678-5")`, while `Rut.parse("12 345678-5")` reports `"invalido"`.
A 500k-input fuzz found 205 such complete-RUT mismatches — **all whitespace,
zero DV-calculation divergence**. So this is a *strictness-consistency gap*,
not a mis-validation: the DV is always checked correctly. The cost is
surprise — `ESTRICTO` means two different things depending on which entry point
you call, and a tool that advertises rigor should not have that ambiguity.

## Current state

- `rutificador/rut.py`:
  - `Rut.__init__` line 436: `self.cadena_rut, _ = _limpiar_entrada(str(rut).strip())`
    — `_limpiar_entrada` (in `utils.py:178-203`) calls `re.sub(r"\s+", "", ...)`,
    removing ALL whitespace **regardless of mode** (the constructor doesn't even
    take a `modo`; it uses `ValidadorRut()` = `ESTRICTO` by default).
  - `Rut.normalizar` → `_verificar_espacios` (lines 100-114): in `ESTRICTO`
    mode appends `CARACTERES_INVALIDOS` and returns `False` (→ invalid) when
    `re.search(r"\s", cadena_original)` matches.
- `rutificador/utils.py:178-203`: `_limpiar_entrada` — shared cleaner.
- The 205 mismatches are exactly inputs with internal/leading whitespace that
  the constructor silently cleans but `parse(ESTRICTO)` rejects.

The whitespace handling is the **only** dangerous-class divergence. The other
large mismatch bucket (bare base, no DV: `Rut("12345678")` succeeds while
`parse` says `"posible"`) is **by design** — the constructor's job is to build
a canonical `Rut` from a base, computing the DV. Do **not** change that; this
plan is about whitespace only.

## Step 1 — DECISION GATE (resolve before coding)

There are three defensible resolutions. They have very different blast radius.
**Do not pick on your own.** Present this to the operator and get an explicit
choice:

- **Option A — Document, don't change behavior (least breaking, default).**
  The constructor *always normalizes* input (strips whitespace, etc.) and is
  the lenient builder; `parse()` *classifies* input under a `modo` and is the
  strict checker. Make this contract explicit in the docstrings of `Rut`,
  `Rut.__init__`, and `Rut.parse` and in CLAUDE.md, and update the
  characterization test from plan 002 to assert the documented contract. **No
  runtime behavior changes. Zero breakage.**

- **Option B — Make the constructor honor `ESTRICTO` whitespace rejection.**
  When the active validador is in `ESTRICTO` mode, reject internal whitespace
  in the constructor instead of stripping it. **Breaking**: any caller passing
  `Rut("12 345 678-5")` today gets a value; afterward gets `ErrorValidacionRut`.
  Requires a minor-version bump and a CHANGELOG entry.

- **Option C — Make `parse(ESTRICTO)` lenient on whitespace** to match the
  constructor. Changes `parse()` classification (whitespace inputs become
  `"valido"`). Also a behavior change, and arguably weakens `ESTRICTO`.

**Recommended: Option A** — it eliminates the *ambiguity* (the real problem)
without breaking anyone, and it is the honest description of what the two
methods are actually for. The rest of this plan is written for Option A; if the
operator picks B or C, STOP and request a revised plan.

**Verify (gate passed)**: you have a recorded operator decision. If it is not
"A", STOP.

## Commands you will need

| Purpose   | Command                                                        | Expected |
|-----------|----------------------------------------------------------------|----------|
| Setup     | `source .venv/bin/activate` (if present) **or** `pip install -r requirements-dev.txt && pip install -e .` | env ready |
| Tests     | `python -m pytest -W error::DeprecationWarning -q tests/`      | all pass |
| Lint/format/types | `ruff check rutificador/ && ruff format --check rutificador/ && mypy rutificador/ --ignore-missing-imports` | all pass |

## Scope (Option A)

**In scope**:
- `rutificador/rut.py` — docstrings of `Rut`, `Rut.__init__`, `Rut.parse`,
  `Rut.normalizar` only (prose, no logic).
- `CLAUDE.md` — the one sentence describing `parse()` vs the constructor.
- `tests/test_consistencia_parse.py` — update
  `test_divergencia_espacios_documentada` into a *contract* test asserting the
  documented behavior (constructor lenient on whitespace, parse strict).

**Out of scope**:
- Any validation logic in `rut.py`, `validador.py`, `utils.py` — Option A
  changes **no behavior**.
- The bare-base / missing-DV behavior — by design, leave it.
- README marketing copy beyond accuracy fixes.

## Git workflow

- Branch: `advisor/003-constructor-parse-consistency`
- Commit: `docs: clarify Rut() builder vs Rut.parse() classifier contract`
- Do NOT push/PR unless instructed.

## Steps (Option A)

### Step 2: Document the contract in `rut.py`

In the class docstring of `Rut` and in `Rut.__init__`'s docstring, state
plainly that the constructor **normalizes** input — including stripping
internal/edge whitespace and accepting a bare base (computing the DV) — and is
the lenient builder. In `Rut.parse` / `Rut.normalizar` docstrings, state that
they **classify** input under the given `modo`, and that `ESTRICTO` rejects
whitespace (use `FLEXIBLE` to accept-and-warn). Cross-reference each from the
other.

**Verify**: `ruff format --check rutificador/ && mypy rutificador/ --ignore-missing-imports`
→ formatted, `Success`.

### Step 3: Fix the contract sentence in CLAUDE.md

Update the line in CLAUDE.md that calls `parse()` "the exception-safe
alternative" so it instead says `parse()` is the exception-safe **classifier**
(returns a `ValidacionResultado` with an `estado`), distinct from the
constructor which is the **builder** that normalizes input and raises on
invalid. One or two sentences.

**Verify**: `grep -n "parse" CLAUDE.md` shows the updated wording.

### Step 4: Turn the divergence test into a contract test

In `tests/test_consistencia_parse.py`, rewrite
`test_divergencia_espacios_documentada` (added in plan 002) as
`test_contrato_builder_vs_clasificador`, asserting the *documented* contract:
the constructor strips whitespace and builds a valid `Rut`; `parse(ESTRICTO)`
classifies the same whitespace input as `"invalido"`; and `parse(FLEXIBLE)`
classifies it as `"valido"` with a `NORMALIZACION_ESPACIOS` warning. (Confirm
the FLEXIBLE behavior empirically first with
`python -c "from rutificador.rut import Rut; from rutificador.config import RigorValidacion as R; r=Rut.parse('12 345678-5', modo=R.FLEXIBLE); print(r.estado, [w.codigo for w in r.advertencias])"`.)

**Verify**: `python -m pytest -q tests/test_consistencia_parse.py` → all pass.

## Done criteria (Option A)

- [ ] `python -m pytest -W error::DeprecationWarning -q tests/` exits 0
- [ ] Docstrings of `Rut`, `Rut.__init__`, `Rut.parse` mention the
      builder-vs-classifier distinction (`grep -n "normaliza\|clasific" rutificador/rut.py`)
- [ ] CLAUDE.md no longer calls `parse()` merely "the exception-safe
      alternative" without the builder/classifier distinction
- [ ] `tests/test_consistencia_parse.py` has `test_contrato_builder_vs_clasificador`
- [ ] `git diff --stat` shows **no logic change** in `rut.py`/`validador.py`/
      `utils.py` (only docstring lines) — verify by reading the diff
- [ ] `ruff check`, `ruff format --check`, `mypy` all pass
- [ ] `plans/README.md` status row updated

## STOP conditions

- The operator decision in Step 1 is **not** Option A → STOP, request a revised
  plan for B or C (those change behavior, need a version bump + CHANGELOG, and
  must re-run the plan-002 characterization suite to see exactly which cases
  flip).
- The drift check shows `rut.py` whitespace handling already changed.
- Any verification fails twice after a reasonable fix attempt.

## Maintenance notes

- This is the *tactical* resolution. The *strategic* one is plan 006 (single
  parse core), which would make the constructor delegate to `parse()` and
  eliminate the divergence class entirely — at which point this documented
  contract either holds for free or is superseded. If 006 is scheduled, this
  plan is still worth doing first (cheap, ships clarity now) but note the
  overlap in the PR.
- If Option B/C is ever chosen later, it is a **breaking** change: bump the
  minor version, add a CHANGELOG entry, and update every characterization case
  from plan 002 that flips.
