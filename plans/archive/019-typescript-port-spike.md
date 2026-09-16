# Plan 019: Spike — port TypeScript del validador core con gate de conformidad

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat d6c28d8..HEAD -- docs/conformidad.md tests/vectors/conformance.json tests/vectors/schema.json scripts/conformance.py`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P1
- **Effort**: S–M (spike, time-boxed)
- **Risk**: LOW (no toca código del repo salvo `plans/`)
- **Depends on**: none (usa el harness de plan 018, ya DONE)
- **Category**: direction
- **Planned at**: commit `d6c28d8`, 2026-09-15

## Why this matters

El ROADMAP a largo plazo pide un port cross-platform del validador
(Rust → WASM, TypeScript, paquete npm `@tooltician/rutificador`) para
validación client-side en navegadores, Deno y Cloudflare Workers. Hasta el
plan 018 eso era inviable por falta de contrato; hoy existe: vectores
versionados, JSON Schema, runner standalone y workflow que publica los
vectores como artifact. Este spike responde una sola pregunta con evidencia:
¿cuánto cuesta un port TypeScript fiel y qué forma de empaquetado conviene
(repo separado vs. directorio monorepo)? El resultado es una decisión
go/no-go documentada, no código productivo. Nota: el spike 017 rechazó PyO3
por rendimiento FFI — este spike tiene un motivo distinto (distribución, no
velocidad), así que ese rechazo no aplica aquí.

## Current state

Los hechos que el ejecutor necesita, inlineados:

- Contrato de conformidad obligatorio (`ROADMAP.md:61-65`):
  > Contraro de conformidad obligatorio: `docs/conformidad.md` y
  > `tests/vectors/conformance.json` (harness versionado, plan 018).
- `docs/conformidad.md` — contrato para ports: los vectores son la fuente
  canónica de verdad; el runner `scripts/conformance.py` se adapta
  reemplazando dos funciones (`dv_implementation`,
  `validation_implementation`); exit code `0` = conforme.
- `tests/vectors/conformance.json` — hoy `version 1.0.0`, `spec_version 1.0`,
  con 12 casos en `casos_dv` (`{"base": "12345678", "dv_esperado": "5"}`) y
  15 casos en `casos_validacion`
  (`{"entrada": "12.345.678-5", "modo": "estricto",
  "estado_esperado": "valido", "normalizado": "12345678-5"}`).
- `tests/vectors/schema.json` — JSON Schema draft 2020-12 del formato.
- `scripts/conformance.py:18-44` — sección de adaptación; el resto del
  script (carga de vectores, comparación, reporte, exit codes) es lógica
  portable que el port debe replicar. Interfaz a replicar:
  `dv_implementation(base: str, config: dict) -> str` y
  `validation_implementation(entrada: str, modo: str, config: dict) -> dict`
  con `{estado, normalizado, codigos_error}`, donde `estado` es uno de
  `valido | invalido | posible | incompleto` y `modo` es
  `estricto | flexible`.
- `.github/workflows/conformance.yml` — publica `dist/vectors/` como
  artifact `rutificador-conformance-vectors`; el port lo consumirá desde ahí.
- `docs/especificacion-reglas-rut.md` — especificación formal del algoritmo
  (módulo 11, factores cíclicos 2–7, `dv = 11 - (suma % 11)`; `11 → 0`,
  `10 → K`). Leerla antes de escribir cualquier línea TypeScript.
- Precedente de spike: `plans/017-SPIKE-NOTES.md` — su §5 a favor señala
  que el código Rust es portable a `wasm-pack`; su §6 recomienda no-go solo
  como optimización Python. Si el spike TS considera reutilizar esa
  implementación Rust vía WASM en vez de TS puro, debe decirlo y justificarlo
  en las notas.
- Convención de spikes del repo: notas en `plans/NNN-SPIKE-NOTES.md`
  (ver `plans/017-SPIKE-NOTES.md` y `plans/006-SPIKE-NOTES.md` como ejemplo
  de estructura: setup, implementación, validación, resultados, decisión).

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---------|---------|------------|---------------------|
| Toolchain check | `node --version && npm --version` | declared | ambas imprimen versión (Node ≥20) |
| TS check (si se usa tsc) | `npx -y typescript@5 tsc --noEmit <dir-tmp>/*.ts` | declared | exit 0, sin errores |
| Vectors | `python3 -c "import json; d=json.load(open('tests/vectors/conformance.json')); print(d['version'], len(d['casos_dv']), len(d['casos_validacion']))"` | declared | `1.0.0 12 15` (o valores mayores si crecieron — anotar) |
| Nombre npm | `npm view @tooltician/rutificador version` | declared | error 404 / E404 = nombre libre; una versión = nombre ocupado |
| Drift check | `git diff --stat d6c28d8..HEAD -- <paths del drift check>` | declared | vacío |

## Scope

**In scope** (los únicos archivos del repo que puedes modificar/crear):

- `plans/019-SPIKE-NOTES.md` (crear — el producto del spike)
- `plans/README.md` (solo tu fila de estado, al final)

**Out of scope** (NO tocar aunque parezca relacionado):

- Todo `rutificador/` — el spike no cambia la implementación Python.
- `tests/vectors/*`, `scripts/*`, `docs/*` — el contrato no se modifica
  en un spike; si encuentras un bug en vectores o runner, anótalo en las
  notas y STOP (ver condiciones).
- `pyproject.toml`, `requirements-dev.txt`, workflows — sin cambios de
  dependencias ni CI en este repo.
- No crear directorios `packages/`, `ts/` ni archivos del port dentro del
  repo. Todo el prototipo vive en `/tmp/ts-port-spike/` (desechable).

## Git workflow

- Branch: `advisor/019-typescript-port-spike`
- Commits pequeños; estilo de mensaje: conventional commits como en
  `git log` (ej.: `docs(planes): agregar notas del spike TS 019`).
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 0: Confirmar baseline y toolchain

1. Corre el drift check del encabezado. Debe salir vacío.
2. Lee completos `docs/especificacion-reglas-rut.md`,
   `docs/conformidad.md` y `tests/vectors/schema.json`.
3. Corre el check de toolchain (`node`, `npm`) y el comando de vectores.
   Anota versiones de Node/npm y de vectores para las notas.

**Verify**: drift vacío; `node --version` ≥20; vectores `1.0.0 12 15`
(o anota los valores reales si crecieron).

### Step 1: Implementar el núcleo TS en /tmp

En `/tmp/ts-port-spike/` (crear el directorio; nunca dentro del repo),
escribe `rut.ts` con dos funciones puras que repliquen la especificación:

- `calcularDV(base: string): string` — módulo 11, factores cíclicos
  `[2,3,4,5,6,7]`, `dv = 11 - (suma % 11)`; `11 → "0"`, `10 → "K"`.
- `validar(entrada: string, modo: "estricto" | "flexible"): { estado, normalizado, codigos_error }` — cubre al menos los 15 casos de
  `casos_validacion` (los 4 estados y ambos modos deben ser alcanzables).

No agregues dependencias: solo TypeScript/Node estándar. Si algún caso del
vector exige semántica que la especificación no describe con claridad,
anótalo y continúa con el resto (la laguna va a las notas, no se improvisa
semántica).

**Verify**: los archivos existen en `/tmp/ts-port-spike/` y
`npx -y typescript@5 tsc --noEmit /tmp/ts-port-spike/*.ts` sale con exit 0.
(Si `tsc` no puede correr offline, usa `node --check` sobre la versión
`.mjs` equivalente y anótalo.)

### Step 2: Correr los vectores de conformidad contra el prototipo

Escribe `/tmp/ts-port-spike/run.mjs` que cargue
`<repo>/tests/vectors/conformance.json`, ejecute los 27 casos contra las
funciones del paso 1 con la misma regla de comparación que
`scripts/conformance.py:79-87` (estado exacto; `codigo_error` contenido si
el caso lo trae; `normalizado` exacto si el caso lo trae) e imprima
`PASS/FAIL` por caso más un resumen `X/27`, con exit code `0` si todo pasa
y `1` si hay fallos.

**Verify**: `node /tmp/ts-port-spike/run.mjs` → `27/27` y exit `0`.
Guarda la salida completa: irá pegada en las notas.

### Step 3: Evaluar empaquetado y CI del port

Sin escribir código del port en el repo, investiga y anota:

1. Disponibilidad del nombre (`npm view @tooltician/rutificador version`).
2. Opción A (repo separado) vs. opción B (directorio en este monorepo):
   versionado independiente de vectores (`version` en conformance.json) vs.
   releases sincronizados; quién corre el gate de conformidad y dónde;
   impacto en el workflow `publish-package.yml` actual.
3. Bosquejo del workflow CI del port (checkout, descarga del artifact
   `rutificador-conformance-vectors` o copia del JSON, validación contra
   `schema.json`, `node run.mjs`, exigir exit 0). Solo bosquejo en las
   notas, no archivos workflow reales.
4. Estimación gruesa del trabajo restante tras el spike (archivos,
   tests, docs, release npm) en S/M/L con una línea de justificación.

**Verify**: tienes las tres respuestas escritas (nombre, A-vs-B con
recomendación, bosquejo CI, estimación).

### Step 4: Escribir `plans/019-SPIKE-NOTES.md`

Estructura obligatoria (sigue `plans/017-SPIKE-NOTES.md`):

1. Setup (versiones Node/npm/tsc, commit base, versión de vectores).
2. Implementación (qué cubre el prototipo `/tmp`, decisiones tomadas).
3. Validación (salida completa del run del paso 2 pegada).
4. Empaquetado y CI (resultados del paso 3).
5. Decisión **go / no-go / go-condicional** en una línea + 3–5 factores.
6. Si go: esquema del plan de construcción 020-bis (fases y done
   criteria en viñetas, sin escribir ese plan).

**Verify**: el archivo existe y contiene las 6 secciones; la decisión está
en una línea citable.

## Test plan

Este es un spike: no se agregan tests al repo. La evidencia es el run de
conformidad del paso 2 (27/27, exit 0) cuya salida queda pegada en las
notas. Si algún caso falla y la causa es un bug del prototipo, corrígelo
en `/tmp` y re-ejecuta hasta verde. Si la causa está en los vectores o la
especificación, STOP (ver abajo).

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `git diff --name-only d6c28d8...HEAD` lista solo `plans/019-SPIKE-NOTES.md`
  (más `plans/README.md` por la fila de estado).
- [ ] `plans/019-SPIKE-NOTES.md` contiene las 6 secciones y una línea de
  decisión `Decisión: go|no-go|go-condicional`.
- [ ] Las notas pegan una salida de run con `27/27` (o N/N con N anotado y
  justificado si los vectores crecieron) y exit `0`.
- [ ] `plans/README.md` fila 019 actualizada.
- [ ] Nada en `/tmp` es referenciado como entregable; el repo no contiene
  código TypeScript.

## STOP conditions

Stop and report back (do not improvise) if:

- `node`/`npm` no existen en el entorno (no instales nada global; repórtalo
  y propone re-ejecutar el spike donde haya Node ≥20).
- El nombre `@tooltician/rutificador` ya está ocupado por un tercero (la
  recomendación de empaquetado debe cambiar).
- Los vectores o la especificación no describen un caso (laguna real del
  contrato): no inventes semántica; anota el caso y sigue con el resto, y
  si bloquea el 27/27, STOP con el caso citado.
- La comparación exige tocar `rutificador/`, `tests/vectors/*` o
  `scripts/*` para pasar: STOP, eso es un hallazgo contra el contrato, no
  parte del spike.
- Un paso de verificación falla dos veces tras un intento razonable de
  corrección en `/tmp`.

## Maintenance notes

- Si el veredicto es go, el plan de construcción debe exigir el gate de
  conformidad en CI del port desde el día uno (exit 0 bloqueante), o el
  drift TS↔Python es cuestión de tiempo.
- Cada release de vectores (`version` en `conformance.json`) obliga a
  re-correr el gate en ambos lados; anótalo como dependencia permanente.
- **Deferred:** publicar el paquete npm, workflow de release con
  provenance (equivalente SLSA), y página de docs para el port — todo
  pertenece al plan de construcción, no a este spike. Cada diferido en su
  línea: **Deferred:** release npm — lo desbloquea el go de este spike.
  **Deferred:** docs del port (`docs/` + nav mkdocs) — lo desbloquea el
  go de este spike.
