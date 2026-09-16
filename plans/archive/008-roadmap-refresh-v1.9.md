# Plan 008: Actualizar ROADMAP — cerrar v1.7/v1.8, definir v1.9

> **Executor instructions**: Follow this plan step by step. Run every verification
> command and confirm the expected result before moving to the next step. If
> anything in the "STOP conditions" section occurs, stop and report — do not
> improvise. When done, update the status row for this plan in
> `plans/README.md`.

> **Drift check (run first)**: `git diff --stat aaca8c4..HEAD -- ROADMAP.md plans/`
> If `ROADMAP.md` changed since this plan was written, compare the "Current
> state" excerpts against the live code before proceeding; on a mismatch, treat
> it as a STOP condition.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: docs / direction
- **Planned at**: commit `aaca8c4`, 2026-07-14

## Why this matters

El `ROADMAP.md` lista v1.7 y v1.8 con checkboxes vacíos, pero 5 de 8 items ya
están completos o formalmente rechazados con decisión documentada. La
desconexión entre el documento y la realidad confunde a contribuyentes y vuelve
inútil el roadmap como herramienta de coordinación. Actualizarlo tilda los
items cerrados, define v1.9 con 2-3 objetivos concretos extraídos de este mismo
ciclo de auditoría, y restaura su valor como documento vivo.

## Current state

- `ROADMAP.md:9-27` — v1.7: los 4 checkboxes están sin marcar. Plan 007
  (`plans/README.md:26`) documenta las decisiones: mutmut REJECTED,
  import-linter ADOPTED, pyperf REJECTED, uv REJECTED.
- `ROADMAP.md:30-42` — v1.8: MkDocs y benchmark CI ya existen pero los
  checkboxes siguen vacíos. La referencia `plans/007-segunda-fase...` ya está
  en el roadmap.
- `.github/workflows/docs.yml` — CI que despliega MkDocs a GitHub Pages en
  push a master.
- `.github/workflows/benchmark-regression.yml` — CI de regresión de
  rendimiento (no bloqueante, umbral 20%).
- `.github/workflows/ci.yml:12` — Python 3.14 en matriz con
  `continue-on-error`.
- `.github/workflows/ci.yml:89` — mypy aún usa `--ignore-missing-imports`, no
  `--strict`.

Convenciones del repo: mensajes de commit en español con Conventional Commits
(`feat:`, `docs:`, `chore:`). El ROADMAP usa `- [ ]` / `- [x]` para checkboxes.

Ejemplo de commit del repo: `aaca8c4 feat: ejecutar plan 007 + roadmap v2.0 +
benchmarks CI + documentación`.

## Commands you will need

| Purpose       | Command                      | Expected on success     |
|---------------|------------------------------|-------------------------|
| Verify doc    | `python -c "print('ok')"`    | ok (no-op, plan is docs-only)  |

## Scope

**In scope** (the only files you should modify):
- `ROADMAP.md`

**Out of scope** (do NOT touch):
- Cualquier archivo `.py`, `pyproject.toml`, workflows, tests — este plan es
  solo documentación.
- `CHANGELOG.md` — el changelog registra releases, no cambios de roadmap.
- Otros planes en `plans/` — no modificar contenido de otros planes.

## Git workflow

- Branch: `advisor/008-roadmap-refresh`
- Commit: un solo commit con mensaje `docs(roadmap): cerrar v1.7/v1.8 completados, definir v1.9`
- No hacer push ni abrir PR a menos que el operador lo indique.

## Steps

### Step 1: Marcar como completados los items de v1.7

En `ROADMAP.md`, cambiar los 4 checkboxes de la sección v1.7 de `- [ ]` a
`- [x]` y añadir entre paréntesis la decisión:

```
- [x] **Mutation testing con `mutmut`** ... (REJECTED — incompatible Python
  3.12, plan 007)
- [x] **Límites arquitectónicos con `import-linter`** ... (ADOPTED — 3
  contratos en `pyproject.toml`)
- [x] **Benchmarks rigurosos con `pyperf`** ... (REJECTED — pytest-benchmark
  superior, plan 007)
- [x] **Spike de migración a `uv`** ... (REJECTED — Poetry lockfile
  incompatible, plan 007)
```

### Step 2: Marcar como completados los items de v1.8 que ya existen

En la sección v1.8, cambiar:

```
- [x] **Sitio de documentación con MkDocs Material** — desplegado en GitHub
  Pages vía `.github/workflows/docs.yml`.
- [x] **Gate de regresión de rendimiento en CI** — implementado en
  `.github/workflows/benchmark-regression.yml` (no bloqueante, umbral 20%).
- [x] **Python 3.14 first-class** — en matriz CI con `continue-on-error`;
  pendiente remover el flag cuando 3.14 sea estable.
- [ ] **Strict mypy progresivo** — pendiente. Ver plan 009.
```

El único item que queda sin marcar es mypy strict, con referencia al plan 009.

### Step 3: Añadir sección v1.9 con los nuevos objetivos

Insertar después de la sección v1.8, antes de v2.0:

```markdown
## v1.9 (Q4 2026) — Pulido de API, CLI e infraestructura

- [ ] **mypy --strict progresivo por módulo**: habilitar reglas estrictas
  incrementalmente empezando por `utils.py`, `errores.py`, `config.py`,
  `validador.py`. Referencia: `plans/009-mypy-strict-core.md`.
- [ ] **Paridad CLI: comando `enmascarar --token`**: exponer tokenización
  HMAC-SHA256 desde la CLI, con soporte para `--clave` (y variable de entorno
  `RUTIFICADOR_TOKEN_KEY`). Referencia: `plans/010-cli-tokenize-parity.md`.
- [ ] **Spec formal de reglas de validación RUT**: documento de especificación
  con test vectors canónicos exportables (JSON/YAML), prerrequisito para ports
  cross-platform. Referencia: `plans/011-spec-formal-reglas-rut.md`.
- [ ] **Infraestructura de i18n para mensajes de error**: envolver
  `CATALOGO_ERRORES` en función locale-aware (`idioma="es"|"en"`), sin romper
  API. Referencia: `plans/012-i18n-errores.md`.
```

### Step 4: Actualizar la fecha de última modificación

Al final del archivo, actualizar:

```
*Última actualización: 2026-07-14 · v1.6.1*
```

(ya está en esa fecha, pero verificar que sea consistente).

**Verify**: `grep "Última actualización" ROADMAP.md` debe mostrar la fecha
correcta.

## Done criteria

- [ ] Los 4 checkboxes de v1.7 están marcados `[x]` con anotación de decisión
- [ ] Los 3 items de v1.8 que están completos tienen `[x]` con evidencia
- [ ] El item mypy strict de v1.8 sigue con `[ ]` y referencia al plan 009
- [ ] Existe una nueva sección `## v1.9 (Q4 2026)` con 4 checkboxes
- [ ] La fecha de última actualización es correcta
- [ ] Solo se modificó `ROADMAP.md` (`git diff --stat` muestra solo ese archivo)
- [ ] `plans/README.md` status row actualizada

## STOP conditions

- Si `ROADMAP.md` ya tiene los checkboxes de v1.7/v1.8 marcados (otro plan ya
  lo actualizó): reportar que ya está hecho y marcar DONE.
- Si el contenido de v1.7/v1.8 en `ROADMAP.md` difiere significativamente de
  los excerpts de "Current state": reportar el drift y detenerse.
- Si alguno de los planes referenciados (009, 010, 011, 012) no existe en
  `plans/`: no inventar nombres de archivo; usar los slugs exactos de este plan.

## Maintenance notes

- Cada vez que un plan de v1.9 se complete, actualizar el checkbox
  correspondiente en `ROADMAP.md`.
- Cuando v1.9 se libere, mover los items completados a `CHANGELOG.md` y definir
  v1.10 o v2.0 según el progreso de los breaking changes planificados.
- La referencia a planes (009-012) debe mantenerse sincronizada si los slugs
  cambian.
