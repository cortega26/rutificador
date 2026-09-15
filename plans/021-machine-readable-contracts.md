# Plan 021: Contratos machine-readable — JSON Schemas de salidas CLI y error 422 FastAPI

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat d6c28d8..HEAD -- rutificador/cli.py rutificador/contrib/fastapi.py mkdocs.yml`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition. NOTE: this plan must run AFTER
> plan 020 (its schemas snapshot final shapes including `tasa_error` and
> exit code 2). If 020 is not DONE, STOP.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW (solo agrega archivos; no cambia comportamiento)
- **Depends on**: plans/020-cli-data-quality-gate.md (formas finales)
- **Category**: direction
- **Planned at**: commit `d6c28d8`, 2026-09-15

## Why this matters

La CLI emite JSON/JSONL y el contrib FastAPI responde 422 con un `detail`
estructurado, pero ningún artefacto versionado describe esas formas: cada
banco, ETL o frontend que integra rutificador las re-deriva a mano y se
rompe en silencio cuando cambian. Dos JSON Schemas versionados + tests que
los verifican convierten las salidas en contrato, al mismo costo de
mantenimiento que ya paga el repo con `tests/vectors/schema.json`.

## Current state

- Ítem emitido por la CLI (`rutificador/cli.py:194-201`):
  `{"valido": bool, "original": str, "resultado": str, "mensaje_error": str,
  "codigo_error": str, "sugerencia": str}`. Salida `--format json`: lista
  de ítems + objeto `metadata` con `{"audit": {"version", "total",
  "validos", "invalidos", "tiempo_segundos", "tasa_exito"}}`
  (`cli.py:228-237`; tras el plan 020 incluye también `"tasa_error"`).
  `--format jsonl`: un ítem por línea (ver `_EmisionJSONL`,
  `cli.py:114-121`).
- Error FastAPI (`rutificador/contrib/fastapi.py:28-51`):
  `obtener_param_rut` lanza `HTTPException(status_code=HTTP_422,
  detail=[{"loc": ["query", "rut"], "msg": str(exc), "type":
  exc.codigo_error or "valor_error.rut_invalido"}])`. `HTTP_422` es
  `status.HTTP_422_UNPROCESSABLE_CONTENT` o `422` como fallback
  (`fastapi.py:13-20`).
- Precedente de schema versionado: `tests/vectors/schema.json` (draft
  2020-12, con `$id`, `title`, `required`) — imita su estilo
  (`$schema`, `$id` bajo `https://tooltician.com/rutificador/...`,
  `title`, `description`, `required`).
- `jsonschema` NO está en `requirements-dev.txt`; el patrón del repo es
  `pytest.importorskip("jsonschema")`
  (`tests/test_conformance_harness.py:34`). Úsalo: sin cambio de
  dependencias en este plan.
- No existe ningún `schemas/` en el repo; `tests/vectors/schema.json`
  describe vectores de conformidad, NO salidas — son artefactos distintos
  (ver Out of scope).
- Docs: `docs/guia/integraciones.md` existe; nav en `mkdocs.yml`
  (precedente: `Harness de conformidad: conformidad.md`, `mkdocs.yml:89`).

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---------|---------|------------|---------------------|
| Baseline tests | `.venv/bin/python -m pytest tests/ --ignore=tests/benchmarks --ignore=tests/test_benchmark.py -q` | declared | all pass |
| Lint | `.venv/bin/ruff check .` | declared | All checks passed |
| Format | `.venv/bin/ruff format --check .` | declared | already formatted |
| Docs build | `.venv/bin/mkdocs build --strict` | declared | Documentation built |

## Scope

**In scope** (crear; más una línea de nav):

- `schemas/cli-salida.json` (crear)
- `schemas/fastapi-error-422.json` (crear)
- `tests/test_contracts.py` (crear)
- `docs/guia/contratos.md` (crear: qué cubre cada schema, versionado)
- `mkdocs.yml` (solo agregar la línea de nav bajo Guía de Uso)
- `CHANGELOG.md` (entrada bajo `[Unreleased]` o próxima versión menor,
  etiqueta `[DOC]` — docs/contratos, sin cambio de código no hay bump)

**Out of scope** (NO tocar):

- `rutificador/` — este plan no cambia comportamiento; si un output real
  no calza con el schema que describes, el bug es del schema: corrige el
  schema, nunca el código para hacerlo calzar.
- `tests/vectors/schema.json` y `tests/vectors/conformance.json` — el
  contrato de conformidad es otro artefacto con su propio versionado.
- Formatos `text`, `csv`, `xml` de la CLI — sin contrato estable
  (posicionales / presentacionales); documenta la exclusión en
  `docs/guia/contratos.md` en vez de forzarles schema.
- `pyproject.toml` / versión — sin cambios en `rutificador/`, el gate de
  versionado no exige bump (verificado en
  `.github/workflows/version-bump-gate.yml`: solo dispara con cambios en
  `rutificador/`).

## Git workflow

- Branch: `advisor/021-machine-readable-contracts`
- Commit por unidad lógica; estilo conventional commits
  (ej.: `docs(contratos): agregar JSON Schemas de salidas CLI y 422`).
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 0: Establish a green baseline + confirmar 020 DONE

1. Drift check del encabezado → vacío.
2. Confirma que el plan 020 está DONE en `plans/README.md` y que
   `rutificador/cli.py` contiene `max-tasa-error` y `tasa_error`
   (`grep -n "max-tasa-error\|tasa_error" rutificador/cli.py` debe dar
   matches). Si no, STOP: tus schemas nacerían desactualizados.
3. Corre baseline tests.

**Verify**: `grep` con matches; tests verdes.

### Step 1: `schemas/cli-salida.json`

Crea el directorio `schemas/` y el schema draft 2020-12 que describa:

- `item`: objeto con `required: [valido, original]` y las 6 propiedades
  de `cli.py:194-201` con sus tipos (`valido` boolean, resto string).
- `salida_json`: `{items: array de item, metadata: {audit: {version:
  string, total/invalidos/validos: integer ≥0, tiempo_segundos: number,
  tasa_exito: string, tasa_error: number}}}`.
- `salida_jsonl`: el `item` por línea (descríbelo como `item`; el test
  validará línea por línea).

Copia el estilo de `tests/vectors/schema.json` (`$schema`, `$id` =
`https://tooltician.com/rutificador/schemas/cli-salida.json`, `title`,
`description`).

**Verify**: `.venv/bin/python -c "import json;
d=json.load(open('schemas/cli-salida.json'));
print(d['\$schema'], d['version'])"` imprime el draft y una `version`
semántica que TÚ defines empezando en `1.0.0` (los schemas se versionan
independiente de la librería, como los vectores).

### Step 2: `schemas/fastapi-error-422.json`

Mismo estilo, `$id` =
`https://tooltician.com/rutificador/schemas/fastapi-error-422.json`,
`version 1.0.0`. Describe exactamente `fastapi.py:42-50`: objeto con
`detail` = array no vacío de `{loc: ["query", "rut"] (array de string,
minItems 2), msg: string, type: string}`. Incluye `status_code: 422`
como constante en `description` (el código viaja en HTTP, no en el
cuerpo; no lo pongas como propiedad requerida del cuerpo).

**Verify**: el JSON parsea y declara `version 1.0.0`.

### Step 3: `tests/test_contracts.py`

Modelo: `tests/test_conformance_harness.py` (imports al tope,
`pytest.importorskip`, asserts directos). Contenido:

1. `test_schema_cli_valido_contra_metaschema`: carga ambos schemas y
   valida que son JSON válidos con `version` semántica (si `jsonschema`
   falta, `importorskip` salta — igual que el precedente).
2. `test_salida_json_conforme`: corre `cli.main(["validar", "--format",
   "json", archivo_tmp])` con 1 válido + 1 inválido (patrón
   `tmp_path` de `tests/test_cli.py:38-43`), parsea `stdout`
   (usa `capsys`), valida contra `schemas/cli-salida.json`.
3. `test_jsonl_linea_por_linea`: igual con `--format jsonl`; valida
   cada línea no vacía contra la definición `item`.
4. `test_detalle_422_conforme`: usa `TestClient` como en
   `tests/contrib/test_fastapi.py` (lee ese archivo para el patrón
   exacto de app/cliente), pide un RUT inválido, assert `status_code ==
   422` y valida `response.json()["detail"]` contra
   `schemas/fastapi-error-422.json`.

**Verify**: `.venv/bin/python -m pytest tests/test_contracts.py -q` →
`4 passed` (o `4 skipped` si `jsonschema` no está instalado — aceptable
y consistente con el precedente; anota cuál ocurrió).

### Step 4: Docs y changelog

1. `docs/guia/contratos.md`: qué cubre cada schema, qué queda fuera
   (`text`/`csv`/`xml`, por qué), política de versionado independiente
   (`version` dentro de cada schema; bump MINOR al agregar campos
   opcionales, MAJOR al cambiar requeridos), ejemplo de validación en
   Python (3 líneas con `jsonschema.validate`).
2. `mkdocs.yml`: agrega `- Contratos: guia/contratos.md` bajo
   `Guía de Uso` (mismo formato que las entradas existentes).
3. `CHANGELOG.md`: entrada `[DOC]` con los dos schemas.

**Verify**: `.venv/bin/mkdocs build --strict` → `Documentation built`;
`grep -n "contratos" mkdocs.yml` con match.

## Test plan

Ver paso 3: 4 tests en `tests/test_contracts.py` (metaschema, JSON,
JSONL, 422). Patrón estructural: `tests/test_conformance_harness.py`;
patrón CLI-tmp: `tests/test_cli.py:38-43`; patrón TestClient:
`tests/contrib/test_fastapi.py` (leerlo antes de escribir el test 4).

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `.venv/bin/python -m pytest tests/ --ignore=tests/benchmarks --ignore=tests/test_benchmark.py -q` → all pass
- [ ] `ruff check`, `ruff format --check` limpios
- [ ] `mkdocs build --strict` → built
- [ ] `ls schemas/` muestra exactamente `cli-salida.json` y
  `fastapi-error-422.json`, ambos con `version`
- [ ] `git diff --name-only d6c28d8...HEAD` lista solo archivos del Scope
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) if:

- El plan 020 no está DONE o `tasa_error` no existe en `cli.py`.
- Un output real no calza con tu schema: corrige el schema; si tras dos
  intentos sigue sin calzar, STOP con el diff exacto (puede ser un cambio
  de comportamiento no documentado).
- `tests/contrib/test_fastapi.py` no existe o su patrón cambió (para el
  test 4 usa lo que exista; si no hay patrón, STOP).
- `mkdocs build --strict` falla por la nueva página (front-matter, nav).
- Una verificación falla dos veces tras un intento razonable.

## Maintenance notes

- Cada cambio a ítems/metadata/422 obliga a bump de `version` del schema
  afectado + test en verde; el revisor debe exigir ambos juntos.
- Si el plan 020 cambió `metadata["audit"]` después de este plan, los
  schemas quedaron viejos: re-auditar contra `cli.py:228-237`.
- **Deferred:** schemas para `csv`/`xml` — excluidos a propósito (sin
  contrato estable); reabrir solo si se estabilizan sus columnas.
  **Deferred:** publicar schemas en un registry (schemastore) — nada lo
  pide hoy.
