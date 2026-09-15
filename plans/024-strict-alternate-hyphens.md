# Plan 024: ESTRICTO rechaza guiones alternativos (alinear código con spec)

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat b77965a..HEAD -- rutificador/rut.py tests/test_contrato_v1.py tests/test_quick_wins.py tests/vectors/conformance.json docs/especificacion-reglas-rut.md CHANGELOG.md pyproject.toml`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P1 (código contradice spec + docstring + contrato documentado)
- **Effort**: S
- **Risk**: MED (cambia resultados observables en ESTRICTO; red de
  seguridad: suite + vectores + gate de versionado)
- **Depends on**: none (no toca salidas CLI ni schemas del plan 021)
- **Category**: bug
- **Planned at**: commit `b77965a`, 2026-09-15

## Why this matters

La especificación (§5.1), el docstring de `Rut.parse` y el contrato de
modos dicen lo mismo: en ESTRICTO los guiones alternativos se rechazan
con `CARACTERES_INVALIDOS`. El código, en cambio, los acepta en ambos
modos con una simple advertencia (el chequeo ni siquiera recibe el
`modo`). Todo consumidor que confíe en ESTRICTO para "formato canónico"
está aceptando hoy entradas que su propio contrato declara inválidas.
El fix espeja el handling de espacios internos, ya correcto en el mismo
archivo.

## Current state

- Contrato decidido (tres fuentes, mismo veredicto):
  - `docs/especificacion-reglas-rut.md:127-129` (§5.1 ESTRICTO):
    "Rechaza espacios internos → `CARACTERES_INVALIDOS`" y "Requiere
    formato canónico: sin guiones alternativos, sin espacios".
  - `docs/especificacion-reglas-rut.md:93` (§3.3): alternativos "se
    normalizan en modo FLEXIBLE" (solo FLEXIBLE).
  - `rutificador/rut.py:301-303` (docstring `parse`): "``ESTRICTO``:
    rechaza espacios internos, guiones alternativos no limpios y otros
    formatos no canónicos (el código de error es ``CARACTERES_INVALIDOS``
    o ``NORMALIZACION_*`` según el caso)."
- Bug (`rutificador/rut.py:136-143`): `_verificar_guiones_alternativos`
  no recibe `modo` y en ambos modos solo agrega advertencia
  `NORMALIZACION_GUION`. Compáralo con `_verificar_espacios`
  (`rut.py:130-134`), que sí recibe `modo` y en ESTRICTO agrega error
  `CARACTERES_INVALIDOS` y retorna `False`.
- Punto de llamada (`rut.py:252-257`): espacios hace early-return con
  errores; guiones se verifica sin propagar fallo. `normalizar` recibe
  `modo` (`rut.py:232-235`), así que el modo está disponible en el
  punto de llamada. `parse` mapea "hay errores → `invalido`"
  (`rut.py:327`).
- Tests que codifican el bug (deben cambiar; lista cerrada salvo que la
  suite revele más, ver STOP):
  - `tests/test_contrato_v1.py:65-68`
    (`test_unicode_guion_normaliza_con_advertencia`): `Rut.parse` en
    ESTRICTO (default) sobre `"12.345.678–5"` assertiona `valido`.
  - `tests/test_contrato_v1.py:71-74`: el caso `"１２３４５６７８–５"`
    (en-dash sobrevive a NFKC) assertiona `valido`; el caso
    `"１２３４５６７８-５"` (guion fullwidth → NFKC → `-`) sí queda
    `valido` y no se toca.
  - `tests/test_quick_wins.py:32-43`
    (`test_unified_cleaning_excessive_dashes`): constructor `Rut(caso)`
    sobre las 4 variantes assertiona normalización. El constructor usa
    el validador default (ESTRICTO); tras el fix lanza
    `ErrorValidacionRut` para estas entradas.
- Patrón a imitar (`tests/test_contrato_v1.py:168-180`,
  `test_espacios_internos_por_modo`): llama `Rut.normalizar` en ambos
  modos y assertiona `(None, CARACTERES_INVALIDOS)` vs
  `("12345678-5", sin errores, advertencia)`. El import
  `RigorValidacion` ya existe (`test_contrato_v1.py:6`).
- Vectores: `tests/vectors/conformance.json` (`1.0.0`, 12 DV + 15
  validación) NO contiene ningún caso con guion alternativo
  (verificado: 0 matches) — se agregan sin colisionar. Política
  (`docs/conformidad.md`): al agregar casos se incrementa `version`
  (aquí `1.0.0` → `1.1.0`); los valores existentes NO se tocan.
- Versionado (`.github/workflows/version-bump-gate.yml`): el cambio
  toca `rutificador/` → bump obligatorio. Es cambio observable de
  validación (algunas entradas pasan de `valido` a `invalido`) → MINOR:
  `2.1.0` → `2.2.0` (una línea en `[tool.poetry] version` de
  `pyproject.toml`; `version.py` lo lee dinámicamente, no se edita).

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---------|---------|------------|---------------------|
| Baseline tests | `.venv/bin/python -m pytest tests/ --ignore=tests/benchmarks --ignore=tests/test_benchmark.py -q` | declared | all pass |
| Focus tests | `.venv/bin/python -m pytest tests/test_contrato_v1.py tests/test_quick_wins.py tests/test_spec_vectors.py -q` | declared | all pass |
| Conformance runner | `.venv/bin/python scripts/conformance.py` | declared | exit 0, todos PASS |
| Lint/format | `.venv/bin/ruff check .` / `.venv/bin/ruff format --check .` | declared | limpio |
| Types | `.venv/bin/mypy rutificador/ --ignore-missing-imports` | declared | no issues |
| Vectors REPL check | `.venv/bin/python -m pytest tests/test_conformance_harness.py -q` | declared | 5 passed |

## Scope

**In scope**:

- `rutificador/rut.py` (solo `_verificar_guiones_alternativos` + su
  llamada: firma, rama ESTRICTO, early-return)
- `tests/test_contrato_v1.py` (reescribir guion-test + split fullwidth)
- `tests/test_quick_wins.py` (reapuntar dashes-test a FLEXIBLE)
- `tests/vectors/conformance.json` (solo AGREGAR casos + bump
  `version` a `1.1.0`; ningún valor existente se toca)
- `CHANGELOG.md` (entrada `[2.2.0]` `[FIXED]`)
- `pyproject.toml` (solo línea `version`: `2.1.0` → `2.2.0`)

**Out of scope** (NO tocar):

- `docs/especificacion-reglas-rut.md` — ya dice lo correcto; si al
  leerla encuentras otra cosa, STOP en vez de "arreglarla".
- `rutificador/utils.py` (`_limpiar_entrada` sigue normalizando
  guiones — correcto para FLEXIBLE y para el constructor flexible).
- `Rut.__init__` / constructor — NO crearle un modo especial; hereda
  la semántica de `normalizar` como hoy (con strict default, ahora
  lanza ante guiones alternativos: es la consecuencia especificada,
  no un efecto colateral).
- `Rut.mejorar` / `sugestor` — salvo que la suite los señale.
- Plan 021 y sus schemas — no describen outcomes de validación.

## Git workflow

- Branch: `advisor/024-strict-alternate-hyphens`
- Commits por unidad (`fix:` + `test:`); estilo conventional commits
  (ej.: `fix(validador): rechazar guiones alternativos en ESTRICTO`).
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 0: Establish a green baseline

Drift check + suite con ignores en verde sobre el checkout limpio.

**Verify**: drift vacío; all pass.

### Step 1: El fix (espejar `_verificar_espacios`)

En `rutificador/rut.py`, cambia la firma y el cuerpo siguiendo
exactamente el patrón de `_verificar_espacios` (`rut.py:130-134`):

```python
@staticmethod
def _verificar_guiones_alternativos(
    cadena_original: str,
    modo: RigorValidacion,
    errores: list[DetalleError],
    advertencias: list[DetalleError],
    vistos: set[str],
) -> bool:
    if any(simbolo in cadena_original for simbolo in ("_", "–", "—", "−")):
        if modo == RigorValidacion.ESTRICTO:
            errores.append(crear_detalle_error("CARACTERES_INVALIDOS"))
            return False
        Rut._agregar_advertencia(advertencias, vistos, "NORMALIZACION_GUION")
    return True
```

Y el punto de llamada (`rut.py:257`):

```python
if not Rut._verificar_guiones_alternativos(
    cadena_original, modo, errores, advertencias, vistos
):
    return None, errores, advertencias
```

(`RigorValidacion` ya está importado en el módulo; `modo` está en scope
en `normalizar`. No agregues imports.)

**Verify**: `.venv/bin/python -c "
from rutificador import Rut, RigorValidacion
r = Rut.parse('12.345.678–5')
assert (r.estado, [e.codigo for e in r.errores]) == ('invalido', ['CARACTERES_INVALIDOS']), (r.estado, r.errores)
r = Rut.parse('12.345.678–5', modo=RigorValidacion.FLEXIBLE)
assert r.estado == 'valido' and any(a.codigo == 'NORMALIZACION_GUION' for a in r.advertencias)
print('OK')"`.

### Step 2: Actualizar los 3 tests que codifican el bug

1. `tests/test_contrato_v1.py:65-68`: renombra a
   `test_unicode_guion_rechazado_en_estricto`; assert
   `estado == "invalido"` + `_contiene_codigo(res.errores,
   "CARACTERES_INVALIDOS")`. Agrega al lado
   `test_unicode_guion_normaliza_en_flexible` con
   `modo=RigorValidacion.FLEXIBLE` assertionando `valido` +
   `NORMALIZACION_GUION` en advertencias (patrón
   `test_espacios_internos_por_modo`, líneas 168-180).
2. `tests/test_contrato_v1.py:71-74`: deja `"１２３４５６７８-５"`
   assertionando `valido`; mueve `"１２３４５６７８–５"` al nuevo test
   estricto (pasa a `invalido`).
3. `tests/test_quick_wins.py:32-43`: el constructor strict ahora
   lanza para estas entradas. Reapunta el test a FLEXIBLE siguiendo el
   patrón de `test_flexible_mode_with_unicode_spaces` (líneas 46-54:
   `ValidadorRut(modo=RigorValidacion.FLEXIBLE)` + `Rut(caso,
   validador=validador)`), manteniendo el assert
   `str(rut) == "12345678-5"` para las 4 variantes. Revisa los imports
   del archivo (`RigorValidacion`, `ValidadorRut`) y agrégalos si
   faltan, en el estilo existente.

**Verify**: focus tests en verde; si OTRO test falla por el cambio de
comportamiento, evalúalo: si es la misma clase (strict + guion
alternativo esperando `valido`), actualízalo igual y anótalo; si
sugiere semántica distinta (p. ej. algo depende de aceptar `_` en
strict), STOP.

### Step 3: Vectores de conformidad +1.1.0

En `tests/vectors/conformance.json`, AGREGA a `casos_validacion` (no
modifiques ningún caso existente):

- `{"entrada": "12.345.678–5", "modo": "estricto",
  "estado_esperado": "invalido", "codigo_error":
  "CARACTERES_INVALIDOS", "notas": "plan 024: ESTRICTO exige guion
  canónico"}`
- `{"entrada": "12.345.678–5", "modo": "flexible",
  "estado_esperado": "valido", "normalizado": "12345678-5", "notas":
  "plan 024: FLEXIBLE normaliza con advertencia"}` (verifica el
  `normalizado` real antes de fijarlo: si difiere, usa el valor real
  solo si coincide con la regla de normalización; si no, STOP).

Cambia `"version": "1.0.0"` → `"1.1.0"` (top-level del JSON, una
línea). Nada más.

**Verify**: `scripts/conformance.py` exit 0; `test_spec_vectors.py` y
`test_conformance_harness.py` en verde (el schema sigue validando:
solo se agregaron casos del formato ya cubierto).

### Step 4: CHANGELOG + versión + calidad completa

1. `CHANGELOG.md`: sección `## [2.2.0]` (fecha del día) con
   `- [FIXED] ESTRICTO rechaza guiones alternativos
   (_, –, —, −) con CARACTERES_INVALIDOS (antes: valido con
   advertencia); FLEXIBLE sin cambios. Alinea código con
   especificación §5.1 y docstring de Rut.parse.`
2. `pyproject.toml`: `version = "2.1.0"` → `"2.2.0"`.
3. Puerta completa: suite con ignores, `ruff check .`,
   `ruff format --check .`, `mypy rutificador/ --ignore-missing-imports`.

**Verify**: todo verde; `grep -n '^version' pyproject.toml` → `2.2.0`;
`git diff --name-only b77965a...HEAD` lista solo archivos del Scope.

## Test plan

- Tests modificados (paso 2): guion-estricto (invalido +
  CARACTERES_INVALIDOS), guion-flexible (valido + advertencia),
  fullwidth split, dashes-test en FLEXIBLE.
- Tests nuevos vía vectores (paso 3): 2 casos de conformidad que
  corren en `test_spec_vectors.py`, `conformance.py` y el harness.
- Patrón estructural: `test_espacios_internos_por_modo`
  (`test_contrato_v1.py:168-180`).

## Done criteria

Machine-checkable. ALL must hold:

- [ ] Suite con ignores all pass; ruff + format + mypy limpios
- [ ] `Rut.parse('12.345.678–5')` → `invalido`/`CARACTERES_INVALIDOS`;
  con `FLEXIBLE` → `valido` + advertencia
- [ ] `scripts/conformance.py` exit 0 con vectores `1.1.0`
  (17 casos de validación = 15 + 2 nuevos)
- [ ] `git diff --name-only b77965a...HEAD` lista solo archivos del Scope
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) if:

- La spec (§3.3/§5.1) o el docstring no dicen lo citado (drift de
  entendimiento: la decisión cambia por completo).
- Un test fallido sugiere semántica distinta a "strict rechaza"
  (p. ej. dependencia intencional de `_` en strict fuera de los 3
  tests conocidos).
- El `normalizado` real del caso flexible no es `12345678-5` por una
  razón distinta a la normalización estándar.
- Agregar los casos rompe el schema o el harness (forma no cubierta).
- Una verificación falla dos veces tras intento razonable.

## Maintenance notes

- Este cambio endurece validación: cualquier consumidor que pasaba
  guiones alternativos en ESTRICTO verá `invalido`. El CHANGELOG lo
  declara; el revisor del PR debe sopesar si amerita nota adicional en
  `GUIA_MIGRACION_v2.md` (decisión humana, no del ejecutor).
- Los vectores `1.1.0` fluyen solos al gate del futuro port TS
  (plan 019): nada que hacer allá.
- **Deferred:** auditar otros warnings `NORMALIZACION_*` con el mismo
  patrón (¿alguno más debió ser error en strict?) — comparación
  sistemática spec-vs-código pendiente; merece su propio plan solo si
  alguien la pide.
