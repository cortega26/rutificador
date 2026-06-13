# Plan 005: Design — give `RigorValidacion` modes coherent, tested semantics (incl. LEGADO's fate)

> **Executor instructions**: This is a **design/spike plan**, not a
> build-everything plan. Its deliverable is a written design document plus a
> small behavior-probe script — **not** a behavior change. Do not alter
> validation logic. Produce `plans/005-DESIGN-NOTES.md` with the findings and a
> recommendation, then STOP for operator review. Update this plan's row in
> `plans/README.md` when the design doc is written.
>
> **Drift check (run first)**:
> `git diff --stat 278425b..HEAD -- rutificador/config.py rutificador/validador.py rutificador/rut.py`

## Status

- **Priority**: P3
- **Effort**: M (investigation + design; implementation is a follow-up)
- **Risk**: MED (any chosen implementation touches public, advertised behavior)
- **Depends on**: plans/002-characterization-tests.md (the probe reuses its
  helpers); relates to plan 003 (whitespace contract) and plan 006 (parse core)
- **Category**: direction / tech-debt
- **Planned at**: commit `278425b`, 2026-06-12

## Why this matters

The library advertises "modos de validación configurables" as a headline
feature (`rutificador/version.py:70`, README), and `RigorValidacion` exposes
three modes: `ESTRICTO`, `FLEXIBLE`, `LEGADO`. But the modes are **under-
delivered and inconsistent**:

- `LEGADO` is **never branched on** — `grep -rn "RigorValidacion.LEGADO\|== .*LEGADO\|modo == RigorValidacion" rutificador/` finds no comparison against it. Its behavior is whatever falls through: in `ValidadorRut.validar_formato` (validador.py:77) only `FLEXIBLE` triggers input cleaning, while in `Rut._verificar_espacios` (rut.py:108-114) only `ESTRICTO` is special. So `LEGADO` is an accidental hybrid with no defined, tested meaning.
- The constructor (`Rut.__init__`) takes no `modo` at all — it always behaves as
  `ESTRICTO`-with-silent-cleanup (see plan 003). So `FLEXIBLE`/`LEGADO` only
  reach the `parse()`/`normalizar()` path.

This plan decides, with evidence, whether to **flesh out** the modes (define
and test each across both entry points) or **trim** (deprecate `LEGADO`).

## Investigation steps (produce evidence, not code changes)

### Step 1: Build the actual behavior matrix

Write and run a probe (you may keep it as a scratch file you delete after, or
embed its output in the design doc). For a fixed set of representative inputs
(clean RUT, RUT with internal spaces, RUT with alt-hyphen `–`/`_`, RUT with
leading zeros, RUT with thousands separators, bare base, wrong DV), record for
each `RigorValidacion` mode:

- `Rut.parse(s, modo=...)` → `estado`, error codes, warning codes;
- `Rut.normalizar(s, modo=...)` → normalized value, errors, warnings;
- `ValidadorRut(modo=...).validar_formato(s)` → match or exception;
- whether the constructor path can even reach this mode (it can't today).

Use the helpers/inputs from `tests/test_consistencia_parse.py` (plan 002).
Disable logging first (`logging.disable(logging.CRITICAL)`).

**Output**: a markdown table in `plans/005-DESIGN-NOTES.md` showing, per
(input × mode × entry point), the observed result — making the `LEGADO`
ambiguity concrete.

### Step 2: Define the *intended* semantics for each mode

Propose a one-line contract per mode, consistent across `parse`, `normalizar`,
and `validar_formato`. A reasonable strawman to evaluate (challenge it against
the Step 1 matrix and real Chilean-RUT usage):

- `ESTRICTO` — canonical input only; whitespace, alt-hyphens, and stray
  separators are **errors**.
- `FLEXIBLE` — clean-and-warn: normalize whitespace/hyphens/dots, surface a
  `NORMALIZACION_*` warning, still validate the DV strictly.
- `LEGADO` — either (a) an explicit alias of `FLEXIBLE` retained for backward
  compatibility, or (b) deprecated.

### Step 3: Decide LEGADO's fate (this resolves finding F4)

Recommend one, with rationale tied to the Step 1 evidence and the cost of
breakage (it is a **public enum value** — removing it outright is breaking):

- **Deprecate** `LEGADO`: keep the enum member, emit a `DeprecationWarning`
  when it is passed to `parse`/`normalizar`/`ValidadorRut`, document it as an
  alias of `FLEXIBLE`, and schedule removal for v2.0 (matches the existing
  deprecation pattern in `validador.py:148-156` and `exceptions.py:128-136`).
- **Define** `LEGADO`: give it a distinct, tested meaning (e.g. "accept but do
  not warn"). Only choose this if there is a real consumer need — the evidence
  in Step 1 will show whether a coherent niche exists.

### Step 4: Scope the implementation follow-up

In the design doc, list the concrete edits a follow-up plan would make
(files, functions, new tests), the version-bump implication (minor for
deprecation, minor/major depending on FLEXIBLE-in-constructor), and the
interaction with plan 003 (whitespace contract) and plan 006 (parse core) so
they don't collide.

## Deliverable

`plans/005-DESIGN-NOTES.md` containing:

1. The behavior matrix from Step 1.
2. The proposed per-mode contract (Step 2).
3. A LEGADO recommendation with rationale (Step 3) — **this is the answer to
   finding F4**.
4. A scoped implementation checklist + version/coordination notes (Step 4).
5. Open questions for the operator.

## Commands you will need

| Purpose | Command | Expected |
|---------|---------|----------|
| Setup | `source .venv/bin/activate` (if present) **or** `pip install -r requirements-dev.txt && pip install -e .` | env ready |
| Probe | `python plans/_scratch_modes_probe.py` (your scratch script) | prints the matrix |
| Confirm no behavior changed | `python -m pytest -q tests/` | all pass (you changed no `rutificador/` code) |

## Scope

**In scope**: create `plans/005-DESIGN-NOTES.md` (and optionally a scratch probe
script you remove before finishing). **No `rutificador/` source changes.**

**Out of scope**: implementing the chosen design — that is a separate plan the
operator approves after reading the notes. Do not deprecate or rewire any mode
in this plan.

## Done criteria

- [ ] `plans/005-DESIGN-NOTES.md` exists with all five deliverable sections
- [ ] It contains an explicit LEGADO recommendation (deprecate vs define) with
      evidence
- [ ] `git status` shows **no file under `rutificador/` modified**
- [ ] `python -m pytest -q tests/` still green
- [ ] `plans/README.md` status row updated

## STOP conditions

- You find yourself editing `config.py`/`validador.py`/`rut.py` logic — STOP;
  this plan only investigates and documents.
- The Step 1 matrix contradicts the strawman so badly that no coherent mode
  contract exists — that itself is the finding; write it up and STOP for the
  operator.

## Maintenance notes

- F4 (LEGADO) is intentionally resolved *here* rather than in a fix plan,
  because deciding its fate is precisely this design question; a premature
  deprecation elsewhere would pre-empt it.
- If plan 006 (single parse core) is adopted, the mode contract defined here
  must be honored by that single core — coordinate the order so the contract is
  settled before the core is unified.
