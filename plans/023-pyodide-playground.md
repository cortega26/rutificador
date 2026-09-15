# Plan 023: Playground interactivo Pyodide en el sitio de docs

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat d6c28d8..HEAD -- mkdocs.yml docs/index.md docs/guia/`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P3
- **Effort**: S
- **Risk**: LOW (solo docs; sin código de librería)
- **Depends on**: none
- **Category**: direction
- **Planned at**: commit `d6c28d8`, 2026-09-15

## Why this matters

La página principal de docs muestra ejemplos estáticos de validación que
el lector no puede ejecutar. Como el núcleo tiene cero dependencias
runtime, corre bajo Pyodide tal cual: un validador interactivo ("escribe
un RUT, ve el resultado") en el sitio convierte documentación pasiva en
demo, ayuda a adopción y no cuesta empaquetado. Es además la versión
barata de la historia browser mientras el port TypeScript (plan 019) se
decide.

## Current state

- `docs/index.md` (52 líneas): título, ejemplo estático
  (`Rut("12.345.678-5")`, `Rut.parse`), lista de características,
  instalación, licencia. Termina en `docs/index.md:48-52`.
- Páginas de guía en `docs/guia/` (`cli.md`, `instalacion.md`,
  `integraciones.md`, `lotes.md`, `uso-basico.md`); nav en `mkdocs.yml`
  bajo `Guía de Uso` (precedente de alta de página:
  `- Harness de conformidad: conformidad.md`, `mkdocs.yml:89`).
- Plugins activos (`mkdocs.yml:39-54`): `search` (es) y `mkdocstrings`.
  No hay `md_in_html` ni CSP propia: el HTML en bloque dentro del
  markdown pasa al sitio tal cual (Python-Markdown lo preserva).
- El núcleo es 100 % Python puro: el directorio `rutificador/` contiene
  solo `.py` + `py.typed` (sin extensiones C), y el README declara
  "Cero dependencias base — solo estándar de Python" (`README.md:58`).
  Esa es la premisa técnica de todo el plan.
- El workflow `docs.yml` publica a GitHub Pages en push a master (sin
  CSP que bloquee CDN; si el workflow cambió a headers estrictos, ver
  STOP).

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---------|---------|------------|---------------------|
| Baseline docs | `.venv/bin/mkdocs build --strict` | declared | Documentation built |
| Rueda pura | `pip download --no-deps rutificador==2.0.0 -d /tmp/wheelcheck` | declared | un `.whl` sin etiquetas de plataforma (`py3-none-any`) |
| Lint | `.venv/bin/ruff check .` | declared | All checks passed (la página no agrega Python) |
| Drift check | `git diff --stat d6c28d8..HEAD -- <paths>` | declared | vacío |

## Scope

**In scope**:

- `docs/guia/playground.md` (crear: página con el playground)
- `mkdocs.yml` (solo la línea de nav)
- `docs/index.md` (solo un enlace a la nueva página al final de la
  intro; no reescribir la página)
- `plans/README.md` (fila de estado)

**Out of scope** (NO tocar):

- `rutificador/` — la librería no cambia para el playground.
- Vendorear Pyodide o la rueda en el repo (CDN + PyPI siempre; el repo
  no debe crecer megabytes).
- Soporte offline, service workers, o theming del widget más allá de
  clases del tema Material ya cargado.
- El port TypeScript (plan 019): si el spike da go, esta página se
  reevalúa entonces (ver diferidos), no ahora.

## Git workflow

- Branch: `advisor/023-pyodide-playground`
- 1–2 commits; estilo conventional commits (ej.:
  `docs(playground): agregar validador interactivo Pyodide`).
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 0: Baseline + verificar premisas

1. Drift check → vacío.
2. `mkdocs build --strict` en verde sobre el checkout limpio.
3. Descarga la rueda a `/tmp/wheelcheck` y confirma nombre
   `rutificador-*.py3-none-any.whl` (pura + versión esperada).
4. Abre `.github/workflows/docs.yml` y confirma que no agrega headers
   `Content-Security-Policy` que bloqueen `cdn.jsdelivr.net` y
   `pypi.org`. Si los hay, STOP.

**Verify**: build verde; rueda `py3-none-any`; sin CSP bloqueante.

### Step 1: Crear `docs/guia/playground.md`

Página en español (idioma del sitio, `mkdocs.yml:11`) con:

1. Párrafo introductorio (qué hace, que corre 100 % en el navegador vía
   Pyodide + la rueda oficial de PyPI; enlace a `docs/conformidad.md`
   como garantía de que el motor es el mismo validado).
2. Un `<input id="rut-input">`, un `<button id="rut-validar">` y un
   `<div id="rut-salida" aria-live="polite">` (ids fijos; el paso 2 los
   referencia — no los renombres después).
3. Un `<script>`: al click, **carga perezosa** de Pyodide desde CDN
   (`https://cdn.jsdelivr.net/pyodide/vX.Y.Z/full/pyodide.js`, fija la
   versión exacta que verifiques en el paso 0 — nunca `latest`), luego
   `micropip.install("rutificador==<versión de pyproject>")`, después
   `Rut.parse` sobre el input y render del `estado`, `normalizado` y
   `codigo_error` en `#rut-salida`. Estados de UI obligatorios:
   `cargando…`, `válido/inválido` (con formato), `error de red` si el
   CDN/PyPI falla. Sin frameworks JS: vanilla + clases del tema.
4. Nota de privacidad de una línea: el RUT nunca sale del navegador
   salvo la descarga del paquete (CDN/PyPI ven la IP, no el RUT).

La carga perezosa al click (no al cargar la página) es requisito, no
detalle: evita penalizar el peso de todo el sitio.

**Verify**: `grep -c 'rut-input\|rut-validar\|rut-salida' docs/guia/playground.md` ≥ 6 (HTML + JS referencian los mismos ids) y
`grep -c 'latest' docs/guia/playground.md` = 0 (versiones fijadas).

### Step 2: Nav + enlace + build

1. `mkdocs.yml`: agrega `- Playground: guia/playground.md` bajo
   `Guía de Uso` (mismo formato que las entradas vecinas).
2. `docs/index.md`: una línea al final de la intro enlazando
   `[pruébalo en el playground](guia/playground.md)`.
3. `.venv/bin/mkdocs build --strict` → `Documentation built`; abre
   `site/guia/playground/` y confirma que el HTML contiene los tres ids
   y el `<script>`.

**Verify**: build exit 0; `grep -o 'id="rut-[a-z]*"' site/guia/playground/index.html`
lista los tres ids.

## Test plan

Docs sin tests Python. Verificación:

- `mkdocs build --strict` exit 0 antes y después (paso 0 y 2).
- Consistencia de ids HTML↔JS por `grep` (paso 1 y 2).
- Prueba manual obligatoria del ejecutor con `mkdocs serve`:
  cargar la página, click sin haber escrito nada (debe mostrar error
  amable, no traceback), validar `12.345.678-5` (válido) y
  `12.345.678-9` (inválido + código). Anota en el commit el navegador
  usado. Si el CDN no es alcanzable desde tu entorno, STOP en vez de
  aprobar a ciegas.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `mkdocs build --strict` → exit 0, `Documentation built`
- [ ] `site/guia/playground/index.html` contiene `rut-input`,
  `rut-validar`, `rut-salida` y el script con versión Pyodide fijada
- [ ] `grep -c latest docs/guia/playground.md` = 0
- [ ] `ruff check .` limpio (garantiza: solo docs + nav tocaron el árbol)
- [ ] `git diff --name-only d6c28d8...HEAD` lista solo archivos del Scope
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) if:

- La rueda de PyPI no es `py3-none-any` (la premisa "puro Python" falla).
- `docs.yml` impone CSP que bloquea el CDN o PyPI.
- El CDN de Pyodide no es alcanzable desde tu entorno (no apruebes la
  prueba manual a ciegas).
- `mkdocs build --strict` falla por la nueva página.
- `docs/guia/` o el formato del nav cambiaron (drift).
- Una verificación falla dos veces tras intento razonable.

## Maintenance notes

- Cada release de la librería: actualizar el pin `rutificador==X.Y.Z`
  en el script (o la demo miente con versión vieja). El revisor debe
  exigirlo junto al bump de `pyproject.toml`.
- Fijar también la versión menor de Pyodide; los upgrades se prueban
  con la checklist manual del Test plan, nunca a ciegas.
- **Deferred:** migrar el playground al port TypeScript si el plan 019
  da go (widget nativo, sin descarga de 10 MB) — lo desbloquea ese
  veredicto. **Deferred:** modo offline/PWA — nadie lo pide hoy.
