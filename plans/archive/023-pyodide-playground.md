# Plan 023: Playground interactivo Pyodide en el sitio de docs

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat d6c28d8..HEAD -- mkdocs.yml docs/index.md docs/guia/ rutificador/procesador.py rutificador/__init__.py pyproject.toml CHANGELOG.md`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.
>
> **Historial 2026-09-15 (intento 1, BLOQUEADO y aprendido)**: el
> playground se construyó y funciona hasta la carga del paquete, pero
> `from rutificador import Rut` falla en Pyodide con
> `ModuleNotFoundError: No module named '_multiprocessing'`, verificado
> en Chrome headless con la rueda real: `rutificador/__init__.py:26`
> importa `.procesador`, y `rutificador/procesador.py:16` hace
> `from concurrent.futures import ProcessPoolExecutor,
> ThreadPoolExecutor` a nivel de módulo, lo que arrastra
> `multiprocessing.queues` → `_multiprocessing` (ausente en Pyodide).
> La premisa "el núcleo corre bajo Pyodide tal cual" es falsa para el
> import de paquete. El desbloqueo es el Step 0b (import perezoso),
> agregado tras el bloqueo. Reutiliza el worktree
> `/tmp/rutificador-exec-023`: la página (`docs/guia/playground.md`),
> la línea de nav y el enlace ya existen SIN commitear — son tu punto
> de partida, no los recrees (el Step 1 ahora es verificación).

## Status

- **Priority**: P3
- **Effort**: S–M (el Step 0b toca el núcleo con gate completo)
- **Risk**: MED (cambio en import-time del paquete; mitigado por proxy
  test + suite + mypy strict + import-linter)
- **Depends on**: plans/024-strict-alternate-hyphens FUSIONADO (orden de
  versiones: 024 libera `2.2.0`; este plan sube a `2.2.1`. La página solo
  funciona con una release PyPI que contenga el Step 0b, así que este
  plan y su release viajan juntos — ver Step 0c).
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

- `rutificador/procesador.py` (solo Step 0b: mover el import de
  `concurrent.futures` a nivel de función + anotación string con
  `TYPE_CHECKING`; nada más)
- `tests/test_import_liviano.py` (crear: proxy test sin multiprocessing)
- `docs/guia/playground.md` (ya existe sin commitear en el worktree de
  re-ejecución; verificar, no recrear)
- `mkdocs.yml` (solo la línea de nav)
- `docs/index.md` (solo un enlace al final de la intro; no reescribir
  la página)
- `pyproject.toml` (solo línea `version`: `2.2.0` → `2.2.1`, Step 0c)
- `CHANGELOG.md` (solo entrada `[2.2.1]`, Step 0c)
- `plans/README.md` (fila de estado)

**Out of scope** (NO tocar):

- `rutificador/` salvo `procesador.py` para el Step 0b — el resto de
  la librería no cambia para el playground.
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

### Step 0b: Import perezoso de `concurrent.futures` (prerrequisito tras el bloqueo)

> **Historial intento 2 (v1, BLOQUEADO)**: mover el import al cuerpo del
> método + anotación string funciona (proxy test verde, mypy strict
> verde, import-linter KEPT), pero rompe 4 tests existentes que
> parchean `rutificador.procesador.ThreadPoolExecutor` /
> `.ProcessPoolExecutor` como atributos de módulo
> (`tests/test_rutificador.py:492,519,603,629`, todos
> `AttributeError`). Editar esos tests queda prohibido (superficie
> privada que otros consumidores podrían usar igual). La v2 de abajo
> conserva compatibilidad total vía `__getattr__` PEP 562. Reutiliza
> el worktree `/tmp/rutificador-exec-023`: el test proxy y la página
> ya existen sin commitear; el cambio va sobre el `procesador.py` ya
> modificado (no revertir la v1, extenderla).

Sin este paso el navegador falla (ver Historial del encabezado).
Objetivo: `from rutificador import Rut` + `Rut.parse(...)` funcionan
aunque `multiprocessing`, `_multiprocessing` y
`concurrent.futures.process` sean inimportables, sin cambiar ningún
comportamiento en CPython Y sin romper a quien acceda a
`rutificador.procesador.ProcessPoolExecutor` (tests y consumidores).

1. Lee `rutificador/procesador.py:1-40` y `:110-140`. Confirma con
   `grep -n "ProcessPoolExecutor\|ThreadPoolExecutor\|concurrent"
   rutificador/procesador.py` todos los usos a nivel de módulo (la
   línea 16 y la anotación de `obtener_clase_ejecutor` son los
   conocidos; si hay más usos runtime a nivel de módulo, STOP).
2. Parte de la v1 (ya hecha en el worktree, verificar, no rehacer):
   el import fuera del nivel de módulo y la anotación string con
   `TYPE_CHECKING`. NUEVO en v2 — agrega al final de
   `rutificador/procesador.py` (antes de `__all__` si existe; si no,
   al final del archivo) un alias perezoso PEP 562:
   ```python
   def __getattr__(nombre: str) -> Any:
       """Alias perezosos para los ejecutores (compatibilidad + Pyodide).

       `from rutificador import Rut` nunca toca estos atributos, así que
       el import del paquete no arrastra `multiprocessing` (ausente en
       Pyodide). Quien los acceda obtiene la clase real bajo demanda.
       """
       if nombre in {"ProcessPoolExecutor", "ThreadPoolExecutor"}:
           from concurrent import futures

           return getattr(futures, nombre)
       raise AttributeError(f"módulo {__name__!r} sin atributo {nombre!r}")
   ```
    (`Any` ya está importado en el bloque `typing` del archivo; si no
    lo estuviera, STOP.) No cambies lógica, nombres ni `__all__`. Los 4
    tests de `tests/test_rutificador.py:492,519,603,629` deben pasar SIN
    modificarlos: `monkeypatch.setattr` y `from ... import ...` siguen
    funcionando vía `__getattr__` en CPython.
    IMPORTANTE (aprendido en intento 3): el `__getattr__` solo NO basta,
    porque `obtener_clase_ejecutor` importa directo desde
    `concurrent.futures` e ignora el atributo parcheado (los 4 tests
    pasan de `AttributeError` a `assert [] == [4]`). El cuerpo del
    método debe resolver vía atributo de módulo para que el parcheo
    surta efecto — forma validada:
    ```python
    modulo = sys.modules[__name__]
    ejecutor_hilos = cast("type[ThreadPoolExecutor]", modulo.ThreadPoolExecutor)
    ejecutor_procesos = cast("type[ProcessPoolExecutor]", modulo.ProcessPoolExecutor)
    ```
    (`cast` ya importado o agrégalo al bloque `typing`; `sys` ya
    importado.) Esto dispara `__getattr__` bajo demanda y mantiene
    mypy strict en verde. NO edites los 4 tests bajo ningún concepto.
3. Crea `tests/test_import_liviano.py`: test que lanza por subprocess
   (`sys.executable -c`, patrón `ejecutar_cli` de
   `tests/test_cli.py:13-24` con `timeout=15`) un snippet que instala
   un `meta_path` finder que lanza `ImportError` ante
   `multiprocessing`, `_multiprocessing` y `concurrent.futures.process`
   (solo esos; NO bloquees `concurrent.futures` entero a ciegas — si el
   import del paquete lo necesitara, el test debe decirlo, no
   ocultarlo), y luego hace `from rutificador import Rut` +
   `Rut.parse("12.345.678-5")` esperando `valido`, y
   `Rut.parse("12.345.678-9")` esperando `invalido`. Assert
   `returncode == 0`. Si el snippet falla por OTRA importación con
   dependencia de multiprocessing en la cadena (distinta de
   `procesador.py:16`), STOP: ampliar el alcance lo decide el revisor.
4. Corre: el proxy test (`tests/test_import_liviano.py`, ya existe —
   verificar, no recrear), los 4 tests de parcheo
   (`tests/test_rutificador.py -k "backend_process or cae_a_threads or
   por_defecto_utiliza or thread_backend"` — ajusta el `-k` a los
   nombres reales leídos del archivo), la suite con ignores,
   `ruff check .`, `ruff format --check .`,
   `mypy --strict rutificador/procesador.py`,
   `mypy rutificador/ --ignore-missing-imports` y `lint-imports`.

**Verify**: proxy test verde; los 4 tests de parcheo verdes SIN
modificarlos; suite, ruff, mypy (strict + general) e import-linter
verdes; importar el paquete sin tocar los alias no importa
`concurrent.futures` (compruébalo: subprocess con el bloqueador que
importe `rutificador.procesador` a secas — debe funcionar).

### Step 0c: Versión, pin y cadena JS (requiere plan 024 fusionado)

La página solo funciona con una release PyPI que contenga el Step 0b,
y el gate de versionado exige bump por el cambio en `rutificador/`.

1. Confirma prerrequisito: `grep -n '^version' pyproject.toml` debe
   dar `2.2.0` (plan 024 fusionado). Si da otro valor, STOP
   (colisión de versiones: este paso asume exactamente 2.2.0).
2. `pyproject.toml`: `2.2.0` → `2.2.1` (PATCH: refactor sin cambio
   observable en CPython). `CHANGELOG.md`: sección `## [2.2.1]`
   (fecha del día) con `- [FIXED] import del paquete ya no arrastra
   multiprocessing (compatibilidad Pyodide, startup más liviano).`
3. Página: `micropip.install("rutificador==2.2.1")` exacto (debe
   coincidir con el bump; la página NO funciona con 2.0.0/2.1.0,
   probado en intento 3).
4. Cadena JS (defecto pendiente del intento 3): la cadena `.then`
   nunca se resolvía aun con descargas 200, mientras la variante
   `await` idéntica completaba. Primero repite la prueba manual con
   la rueda 2.2.1: si ahora completa, era un artefacto del fallo de
   import (excepción no propagada colgando la cadena) — anótalo y
   sigue. Si sigue colgada, depura el tramo mínimo (compara contra la
   variante `await` que sí funciona; reescribir ese tramo con
   `async/await` vanilla está permitido) hasta que la checklist de
   3 casos pase. Si no hay forma mínima de hacerla resolver, STOP.

**Verify**: versión `2.2.1`; pin de la página idéntico; checklist
manual 3/3 en verde de verdad (vacío amable, válido, inválido+código).

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

- [ ] `tests/test_import_liviano.py` en verde + suite con ignores en
  verde + `mypy --strict rutificador/procesador.py` sin issues +
  `lint-imports` con 3 contratos KEPT
- [ ] `mkdocs build --strict` → exit 0, `Documentation built`
- [ ] `site/guia/playground/index.html` contiene `rut-input`,
  `rut-validar`, `rut-salida` y el script con versión Pyodide fijada
- [ ] `grep -c latest docs/guia/playground.md` = 0
- [ ] Checklist manual navegador 3/3 pasando DE VERDAD (vacío amable,
  válido, inválido+código) con la rueda pinneda
- [ ] `pyproject.toml` en `2.2.1` y pin de la página idéntico
- [ ] `ruff check .` limpio
- [ ] `git diff --name-only d6c28d8...HEAD` lista solo archivos del Scope
  (evaluado contra la base real del worktree si difiere; documentar)
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) if:

- La rueda de PyPI no es `py3-none-any` (la premisa "puro Python" falla).
- El proxy test del Step 0b revela otra dependencia de multiprocessing
  en la cadena fuera de `procesador.py:16`, o la v2 (`__getattr__`)
  rompe strict / import-linter / suite (incluidos los 4 tests de
  parcheo SIN modificar) dos veces. NO editar
  `tests/test_rutificador.py` para hacerlo pasar: STOP y reporta.
- `docs.yml` impone CSP que bloquea el CDN o PyPI.
- El CDN de Pyodide no es alcanzable desde tu entorno (no apruebes la
  prueba manual a ciegas).
- `mkdocs build --strict` falla por la nueva página.
- `docs/guia/` o el formato del nav cambiaron (drift).
- Una verificación falla dos veces tras intento razonable.

## Maintenance notes

- Historial intento 3 (2026-09-15, worktree `/tmp/rutificador-exec-023`,
  commit `cc784a8`): v2 funciona (107 tests intactos en verde, strict,
  import-linter, proxy); el navegador probó que NINGUNA rueda publicada
  (2.0.0 ni 2.1.0) contiene el fix → la página exige release con Step
  0b (de ahí el Step 0c). Posible segundo defecto pendiente: la cadena
  `.then` no resolvía aun con descargas 200 mientras `await` sí — el
  Step 0c lo cubre (pudo ser artefacto del import fallido).
- Cada release de la librería: actualizar el pin `rutificador==X.Y.Z`
  en el script (o la demo miente con versión vieja). El revisor debe
  exigirlo junto al bump de `pyproject.toml`.
- Fijar también la versión menor de Pyodide; los upgrades se prueban
  con la checklist manual del Test plan, nunca a ciegas.
- **Deferred:** migrar el playground al port TypeScript si el plan 019
  da go (widget nativo, sin descarga de 10 MB) — lo desbloquea ese
  veredicto. **Deferred:** modo offline/PWA — nadie lo pide hoy.
