# Plan 006: Spike — unify on a single RUT parse core (constructor delegates to `parse`)

> **Executor instructions**: This is a **spike/design plan**. The deliverable is
> an investigation write-up plus an *optional, behind-no-behavior-change*
> proof-of-concept on a throwaway branch — **not** a merged refactor. Produce
> `plans/006-SPIKE-NOTES.md` and STOP for operator review. Update this plan's
> row in `plans/README.md` when the notes are written.
>
> **Drift check (run first)**:
> `git diff --stat 278425b..HEAD -- rutificador/rut.py rutificador/validador.py rutificador/utils.py`

## Status

- **Priority**: P3
- **Effort**: L (the eventual refactor is multi-day; this spike is M)
- **Risk**: HIGH (the eventual refactor touches the most security-critical code
  in the library; the spike itself is low-risk because it changes nothing)
- **Depends on**: plans/002-characterization-tests.md (the safety net);
  supersedes the long-term need for plan 003's manual alignment
- **Category**: direction / architecture
- **Planned at**: commit `278425b`, 2026-06-12

## Why this matters

The library parses the same RUT grammar **twice**, in two independent code
paths:

- **Constructor path**: `Rut.__init__` → `_analizar_y_validar` (rut.py:444-458)
  → `ValidadorRut.validar_formato` / `validar_base` /
  `validar_digito_verificador` (validador.py).
- **Parse path**: `Rut.parse` → `Rut.normalizar` (rut.py:211-334) with its own
  inline tokenizer (`_separar_base_dv`, `_normalizar_puntos`,
  `_normalizar_ceros`, `_normalizar_dv`, `_reconstruir_normalizado`).

This duplication is the root cause of finding F3 (the two paths disagree on
whitespace) and makes every grammar change a two-place edit that can silently
drift. The strategic fix is **one canonical core**: make the constructor a thin
wrapper that calls `Rut.parse(...)` and raises on a non-valid `estado`,
deleting the second implementation. This spike determines whether that is
feasible without changing observable behavior (beyond the deliberate F3
resolution) and at acceptable risk.

## Why a spike and not a direct refactor

These modules are marked `# SECURITY-CRITICAL`. The constructor and `parse`
have subtly different surfaces:

- The constructor accepts `int` and bare-base input and **computes** the DV
  (returns a fully-built `Rut`); `parse` *classifies* and returns `estado`
  (`"posible"` for a bare base, never auto-completing).
- The constructor raises typed exceptions (`ErrorFormatoRut`, `ErrorDigitoRut`,
  `ErrorLongitudRut`) with specific messages that **tests assert on**
  (`grep -rn "ErrorFormatoRut\|ErrorDigitoRut\|ErrorLongitudRut" tests/`).
- `obtener_rut` LRU-caches `Rut` instances; the `RutBase` dataclass and
  `Rut.__repr__` masking must be preserved.

A blind merge would risk changing exception types/messages and the bare-base
contract. The spike maps these surfaces before committing.

## Investigation steps

### Step 1: Inventory the observable contract of the constructor

Produce, in `plans/006-SPIKE-NOTES.md`, a table of everything the constructor
guarantees that `parse` does not currently express:

- Accepted input types (`int`, bare base → auto-DV).
- Exact exception type + `codigo_error` raised per failure class (run a probe
  over malformed inputs; reuse the input set from plan 002).
- Which existing tests assert on those exception types/messages
  (`grep -rn` results).
- The `RutBase` / `digito_verificador` / `__repr__` / `obtener_rut` cache
  invariants that must survive.

### Step 2: Map parse `estado` → constructor outcome

Define the wrapper's intended logic and show it covers every case:

```
res = Rut.parse(valor, modo=...)
match res.estado:
  "valido"     -> build Rut from res.base + res.dv
  "posible"    -> bare base / missing DV: compute DV, build Rut  (preserve today's constructor leniency)
  "invalido"   -> raise the appropriate typed error from res.errores[0].codigo
  "incompleto" -> raise (empty/typeless)
```

Crucially, show how each `res.errores[0].codigo` maps back to the **specific**
existing exception type and message so asserting tests still pass — or list
exactly which tests would need updating and why that is acceptable.

### Step 3: Throwaway proof-of-concept (optional, isolated)

On a scratch branch only, implement the wrapper and run the **full** suite
(especially plan 002's characterization tests) to see precisely what flips.
Record the diff of failures. **Do not keep or merge this** — it is evidence for
the notes. The real implementation is a later, operator-approved plan with its
own version bump.

### Step 4: Risk & effort assessment

In the notes: list the blast radius (functions deleted, tests touched), the
interaction with plan 003 (this supersedes the manual whitespace alignment) and
plan 005 (the unified core must honor the mode contract), the version-bump
implication, and a go / no-go recommendation with rationale. "No-go, keep the
two paths and rely on plan 003's documented contract" is a valid outcome if the
risk outweighs the duplication cost.

## Deliverable

`plans/006-SPIKE-NOTES.md` with: the constructor contract inventory (Step 1),
the estado→outcome mapping incl. exception-fidelity analysis (Step 2), the PoC
failure diff if run (Step 3), and a go/no-go recommendation with blast radius
and coordination notes (Step 4).

## Commands you will need

| Purpose | Command | Expected |
|---------|---------|----------|
| Setup | `source .venv/bin/activate` (if present) **or** `pip install -r requirements-dev.txt && pip install -e .` | env ready |
| Find asserting tests | `grep -rn "ErrorFormatoRut\|ErrorDigitoRut\|ErrorLongitudRut\|codigo_error" tests/` | list |
| PoC suite run (scratch branch only) | `python -m pytest -q tests/` | record pass/fail diff |
| Confirm main branch untouched | `git status` | no `rutificador/` change on the deliverable branch |

## Scope

**In scope**: create `plans/006-SPIKE-NOTES.md` (+ an optional scratch branch
for the throwaway PoC that is **not** merged).

**Out of scope**: any merged change to `rutificador/` source on the working
branch. The actual unification is a separate, approved plan.

## Done criteria

- [ ] `plans/006-SPIKE-NOTES.md` exists with all four deliverable sections
- [ ] It contains an explicit **go / no-go** recommendation with blast radius
- [ ] It enumerates which existing tests assert on constructor exception
      types/messages and how each is handled under the wrapper
- [ ] On the deliverable branch, `git status` shows **no `rutificador/`
      source modified**
- [ ] `plans/README.md` status row updated

## STOP conditions

- The PoC shows the wrapper cannot preserve a typed exception that tests depend
  on without changing the public exception contract → record it as a no-go
  factor and STOP for the operator (do not "fix" tests to force a green).
- You are tempted to merge the PoC — STOP; this plan never merges source.

## Maintenance notes

- If the recommendation is **go**, the follow-up implementation plan must:
  land after plan 005 (mode contract settled), preserve `obtener_rut` caching,
  `RutBase`, `__repr__` masking, and the bare-base auto-DV leniency, and bump
  the version with a CHANGELOG entry. It would render plan 003's manual
  whitespace alignment redundant (the single core decides whitespace once).
- If **no-go**, plan 003's documented contract remains the standing resolution
  for F3, and this spike's notes record why unification was declined so it is
  not re-litigated.
